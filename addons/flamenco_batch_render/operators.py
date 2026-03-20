import bpy
import json
import webbrowser
from pathlib import Path

# Store original materials
_original_materials = {}


def _save_marks_to_scene(scene):
    """Store current marks as a plain JSON custom property.
    This is readable by BlenderTools headlessly (without the addon loaded)."""
    front = [obj.name for obj in scene.objects if obj.type == 'MESH' and obj.batch_render_type == 'FRONT']
    back  = [obj.name for obj in scene.objects if obj.type == 'MESH' and obj.batch_render_type == 'BACK']
    scene["batch_render_marks"] = json.dumps({"front": front, "back": back})


def update_object_display(obj):
    """Update object material preview for marking"""
    global _original_materials

    if obj.type != 'MESH':
        return

    if obj.batch_render_type == 'FRONT':
        if 'batch_front_preview' not in bpy.data.materials:
            mat = bpy.data.materials.new('batch_front_preview')
            mat.use_nodes = True
            mat.diffuse_color = (1.0, 0.2, 0.2, 1.0)
            mat.metallic = 0.0
            mat.roughness = 0.5
        mat = bpy.data.materials['batch_front_preview']
        key = f"{obj.name}_{id(obj)}"
        if key not in _original_materials:
            _original_materials[key] = list(obj.data.materials)
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    elif obj.batch_render_type == 'BACK':
        if 'batch_back_preview' not in bpy.data.materials:
            mat = bpy.data.materials.new('batch_back_preview')
            mat.use_nodes = True
            mat.diffuse_color = (0.2, 0.5, 1.0, 1.0)
            mat.metallic = 0.0
            mat.roughness = 0.5
        mat = bpy.data.materials['batch_back_preview']
        key = f"{obj.name}_{id(obj)}"
        if key not in _original_materials:
            _original_materials[key] = list(obj.data.materials)
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    else:
        key = f"{obj.name}_{id(obj)}"
        if key in _original_materials:
            obj.data.materials.clear()
            for mat in _original_materials[key]:
                obj.data.materials.append(mat)


class MarkObjectFront(bpy.types.Operator):
    """Mark object for front color rendering"""
    bl_idname = "wm.mark_object_front"
    bl_label = "Front"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj is None:
            self.report({'WARNING'}, "Geen object geselecteerd")
            return {'CANCELLED'}
        obj.batch_render_type = 'FRONT'
        update_object_display(obj)
        _save_marks_to_scene(context.scene)
        return {'FINISHED'}


class MarkObjectBack(bpy.types.Operator):
    """Mark object for back color rendering"""
    bl_idname = "wm.mark_object_back"
    bl_label = "Back"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj is None:
            self.report({'WARNING'}, "Geen object geselecteerd")
            return {'CANCELLED'}
        obj.batch_render_type = 'BACK'
        update_object_display(obj)
        _save_marks_to_scene(context.scene)
        return {'FINISHED'}


class UnmarkObject(bpy.types.Operator):
    """Unmark the object"""
    bl_idname = "wm.unmark_object"
    bl_label = "Unmark"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name) if self.object_name else context.active_object
        if obj:
            obj.batch_render_type = 'NONE'
            update_object_display(obj)
            _save_marks_to_scene(context.scene)
            self.report({'INFO'}, f"'{obj.name}' niet meer gemarkeerd")
        return {'FINISHED'}


class ClearAllMarks(bpy.types.Operator):
    """Clear all marks in scene"""
    bl_idname = "wm.clear_all_marks"
    bl_label = "Alles Wissen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.scene.objects:
            if obj.batch_render_type != 'NONE':
                obj.batch_render_type = 'NONE'
                update_object_display(obj)
                count += 1
        _save_marks_to_scene(context.scene)
        self.report({'INFO'}, f"{count} markeringen verwijderd")
        return {'FINISHED'}


class SubmitToFlamenco(bpy.types.Operator):
    """Submit marked objects to Flamenco"""
    bl_idname = "wm.batch_marks_to_flamenco"
    bl_label = "Verzend naar Flamenco"

    def execute(self, context):
        scene = context.scene

        front_objs = [obj for obj in scene.objects if obj.batch_render_type == 'FRONT']
        back_objs  = [obj for obj in scene.objects if obj.batch_render_type == 'BACK']

        if not front_objs and not back_objs:
            self.report({'ERROR'}, "Geen objecten gemarkeerd als Front of Back")
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

        mapping = {}
        for obj in front_objs:
            mapping[obj.name] = scene.batch_front_material
        for obj in back_objs:
            mapping[obj.name] = scene.batch_back_material

        if not mapping:
            self.report({'ERROR'}, "Mapping is leeg")
            return {'CANCELLED'}

        blend_file     = bpy.data.filepath
        material_library = scene.batch_material_library
        output_dir     = Path(scene.batch_output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        job = {
            "name": f"Batch Render — {len(front_objs)} Front, {len(back_objs)} Back",
            "job_type": "material_batch",
            "tasks": [{
                "name": "render_marked_objects",
                "type": "material_batch",
                "settings": {
                    "blend_file": str(Path(blend_file).resolve()),
                    "material_library": str(Path(material_library).resolve()),
                    "object_material_mapping": json.dumps(mapping),
                    "output_directory": str(output_dir.resolve()),
                    "render_width": scene.batch_render_width,
                    "render_height": scene.batch_render_height,
                    "render_samples": scene.batch_render_samples,
                    "render_engine": scene.batch_render_engine,
                }
            }]
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
                job_data = response.json()
                job_id   = job_data.get('id', 'onbekend')
                self.report({'INFO'}, f"Job {job_id} verzonden ({len(front_objs)}F + {len(back_objs)}B)")
                if scene.batch_open_ui_after_submit:
                    webbrowser.open(f"{manager_url}/ui/jobs/{job_id}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Mislukt ({response.status_code}): {response.text[:200]}")
                return {'CANCELLED'}

        except requests.exceptions.ConnectionError:
            self.report({'ERROR'}, f"Kan niet verbinden met Flamenco op {scene.flamenco_manager_url}")
            return {'CANCELLED'}
        except ImportError:
            self.report({'ERROR'}, "requests bibliotheek niet geïnstalleerd")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Fout: {str(e)}")
            return {'CANCELLED'}


def add_object_context_menu(self, context):
    """Add to right-click context menu"""
    layout = self.layout
    layout.separator()
    if context.active_object:
        obj = context.active_object
        layout.label(text="Batch Render", icon='RENDER_RESULT')
        op = layout.operator("wm.mark_object_front", text="Front (Rood)",
                             depress=(obj.batch_render_type == 'FRONT'))
        op.object_name = obj.name
        op = layout.operator("wm.mark_object_back", text="Back (Blauw)",
                             depress=(obj.batch_render_type == 'BACK'))
        op.object_name = obj.name
        if obj.batch_render_type != 'NONE':
            layout.operator("wm.unmark_object", text="Verwijder markering").object_name = obj.name


def register():
    bpy.utils.register_class(MarkObjectFront)
    bpy.utils.register_class(MarkObjectBack)
    bpy.utils.register_class(UnmarkObject)
    bpy.utils.register_class(ClearAllMarks)
    bpy.utils.register_class(SubmitToFlamenco)


def unregister():
    bpy.utils.unregister_class(MarkObjectFront)
    bpy.utils.unregister_class(MarkObjectBack)
    bpy.utils.unregister_class(UnmarkObject)
    bpy.utils.unregister_class(ClearAllMarks)
    bpy.utils.unregister_class(SubmitToFlamenco)
