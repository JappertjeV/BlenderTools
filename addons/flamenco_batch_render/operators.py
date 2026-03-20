import bpy
import json
import webbrowser
from pathlib import Path

_original_materials = {}


def _save_marks_to_scene(scene):
    """Store selected objects as a plain JSON custom property.
    Readable by BlenderTools headlessly (without the addon loaded)."""
    selected = [
        obj.name for obj in scene.objects
        if obj.type == 'MESH' and obj.batch_render_selected
    ]
    scene["batch_render_marks"] = json.dumps({"selected": selected})


def _apply_preview_material(obj):
    """Apply a colored preview material to show the object is selected for rendering."""
    if obj.type != 'MESH':
        return

    if 'batch_render_preview' not in bpy.data.materials:
        mat = bpy.data.materials.new('batch_render_preview')
        mat.use_nodes = True
        mat.diffuse_color = (0.2, 0.8, 0.3, 1.0)  # Groen
        mat.metallic = 0.0
        mat.roughness = 0.5
    mat = bpy.data.materials['batch_render_preview']

    key = f"{obj.name}_{id(obj)}"
    if key not in _original_materials:
        _original_materials[key] = list(obj.data.materials)

    obj.data.materials.clear()
    obj.data.materials.append(mat)


def _restore_original_material(obj):
    """Restore the original materials of the object."""
    if obj.type != 'MESH':
        return
    key = f"{obj.name}_{id(obj)}"
    if key in _original_materials:
        obj.data.materials.clear()
        for mat in _original_materials[key]:
            obj.data.materials.append(mat)


def update_object_display(obj):
    if obj.batch_render_selected:
        _apply_preview_material(obj)
    else:
        _restore_original_material(obj)


class ToggleColorObject(bpy.types.Operator):
    """Selecteer of deselecteer een kleur verander object"""
    bl_idname = "wm.toggle_color_object"
    bl_label = "Kleur Verander Object"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj is None:
            self.report({'WARNING'}, "Geen object gevonden")
            return {'CANCELLED'}
        obj.batch_render_selected = not obj.batch_render_selected
        update_object_display(obj)
        _save_marks_to_scene(context.scene)
        return {'FINISHED'}


class SelectColorObject(bpy.types.Operator):
    """Markeer object als kleur verander object"""
    bl_idname = "wm.select_color_object"
    bl_label = "Selecteer"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj is None:
            return {'CANCELLED'}
        obj.batch_render_selected = True
        update_object_display(obj)
        _save_marks_to_scene(context.scene)
        return {'FINISHED'}


class DeselectColorObject(bpy.types.Operator):
    """Verwijder markering van object"""
    bl_idname = "wm.deselect_color_object"
    bl_label = "Deselecteer"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj is None:
            return {'CANCELLED'}
        obj.batch_render_selected = False
        update_object_display(obj)
        _save_marks_to_scene(context.scene)
        return {'FINISHED'}


class ClearAllColorObjects(bpy.types.Operator):
    """Verwijder alle kleur verander markeringen"""
    bl_idname = "wm.clear_all_color_objects"
    bl_label = "Alles Wissen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.scene.objects:
            if obj.type == 'MESH' and obj.batch_render_selected:
                obj.batch_render_selected = False
                update_object_display(obj)
                count += 1
        _save_marks_to_scene(context.scene)
        self.report({'INFO'}, f"{count} markeringen verwijderd")
        return {'FINISHED'}


class SubmitToFlamenco(bpy.types.Operator):
    """Verzend kleur verander objecten naar Flamenco"""
    bl_idname = "wm.batch_marks_to_flamenco"
    bl_label = "Verzend naar Flamenco"

    def execute(self, context):
        scene = context.scene

        selected_objs = [
            obj for obj in scene.objects
            if obj.type == 'MESH' and obj.batch_render_selected
        ]

        if not selected_objs:
            self.report({'ERROR'}, "Geen kleur verander objecten geselecteerd")
            return {'CANCELLED'}

        if not scene.batch_material_library:
            self.report({'ERROR'}, "Materiaalbibliotheek niet ingesteld")
            return {'CANCELLED'}

        if not scene.batch_output_directory:
            self.report({'ERROR'}, "Output map niet ingesteld")
            return {'CANCELLED'}

        if not bpy.data.is_saved:
            self.report({'ERROR'}, "Sla het Blender-bestand eerst op")
            return {'CANCELLED'}

        mapping = {obj.name: scene.batch_material_name for obj in selected_objs}

        output_dir = Path(scene.batch_output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        job = {
            "name": f"Batch Render — {len(selected_objs)} object(en)",
            "job_type": "material_batch",
            "tasks": [{
                "name": "render_color_objects",
                "type": "material_batch",
                "settings": {
                    "blend_file":              str(Path(bpy.data.filepath).resolve()),
                    "material_library":        str(Path(scene.batch_material_library).resolve()),
                    "object_material_mapping": json.dumps(mapping),
                    "output_directory":        str(output_dir.resolve()),
                    "render_width":            scene.batch_render_width,
                    "render_height":           scene.batch_render_height,
                    "render_samples":          scene.batch_render_samples,
                    "render_engine":           scene.batch_render_engine,
                },
            }],
        }

        try:
            import requests
            manager_url = scene.flamenco_manager_url.rstrip('/')
            response = requests.post(
                f"{manager_url}/api/v3/jobs",
                json=job,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 201:
                job_id = response.json().get('id', 'onbekend')
                self.report({'INFO'}, f"Job {job_id} verzonden ({len(selected_objs)} object(en))")
                if scene.batch_open_ui_after_submit:
                    webbrowser.open(f"{manager_url}/ui/jobs/{job_id}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Mislukt ({response.status_code}): {response.text[:200]}")
                return {'CANCELLED'}

        except requests.exceptions.ConnectionError:
            self.report({'ERROR'}, f"Kan niet verbinden met {scene.flamenco_manager_url}")
            return {'CANCELLED'}
        except ImportError:
            self.report({'ERROR'}, "requests bibliotheek niet geïnstalleerd")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Fout: {str(e)}")
            return {'CANCELLED'}


def add_object_context_menu(self, context):
    layout = self.layout
    layout.separator()
    if context.active_object and context.active_object.type == 'MESH':
        obj = context.active_object
        layout.label(text="Batch Render", icon='RENDER_RESULT')
        is_selected = obj.batch_render_selected
        op = layout.operator(
            "wm.toggle_color_object",
            text="Deselecteer kleur verander" if is_selected else "Selecteer als kleur verander",
            icon='CHECKMARK' if is_selected else 'RESTRICT_SELECT_OFF',
        )
        op.object_name = obj.name


def register():
    bpy.utils.register_class(ToggleColorObject)
    bpy.utils.register_class(SelectColorObject)
    bpy.utils.register_class(DeselectColorObject)
    bpy.utils.register_class(ClearAllColorObjects)
    bpy.utils.register_class(SubmitToFlamenco)


def unregister():
    bpy.utils.unregister_class(ToggleColorObject)
    bpy.utils.unregister_class(SelectColorObject)
    bpy.utils.unregister_class(DeselectColorObject)
    bpy.utils.unregister_class(ClearAllColorObjects)
    bpy.utils.unregister_class(SubmitToFlamenco)
