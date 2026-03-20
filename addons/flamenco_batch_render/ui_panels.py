import bpy


def _draw_object_list(layout, scene):
    """Draw a selectable list of all mesh objects."""
    mesh_objects = sorted(
        [o for o in scene.objects if o.type == 'MESH'],
        key=lambda o: o.name,
    )

    if not mesh_objects:
        layout.label(text="Geen mesh objecten gevonden", icon='INFO')
        return

    col = layout.column(align=True)
    for obj in mesh_objects:
        row = col.row(align=True)
        is_selected = obj.batch_render_selected

        # Checkbox-stijl toggle knop
        op = row.operator(
            "wm.toggle_color_object",
            text="",
            icon='CHECKBOX_HLT' if is_selected else 'CHECKBOX_DEHLT',
            depress=is_selected,
        )
        op.object_name = obj.name

        # Object naam
        row.label(text=obj.name)


class RENDER_PT_batch_render_marks(bpy.types.Panel):
    """Configuratiepanel in Properties → Output"""
    bl_label = "Kleur Verander Objecten"
    bl_idname = "RENDER_PT_batch_marks"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        selected_objs = [o for o in scene.objects if o.type == 'MESH' and o.batch_render_selected]

        # ── Object selectie ────────────────────────────────────────────────
        box = layout.box()
        box.label(
            text=f"Kleur verander objecten: {len(selected_objs)}",
            icon='OBJECT_DATA',
        )
        _draw_object_list(box, scene)
        box.operator("wm.clear_all_color_objects", text="Alles Wissen", icon='TRASH')

        # ── Flamenco verbinding ────────────────────────────────────────────
        box = layout.box()
        box.label(text="Flamenco Manager", icon='NETWORK_DRIVE')
        box.prop(scene, "flamenco_manager_url")
        box.prop(scene, "batch_open_ui_after_submit")

        # ── Materiaal ─────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Materiaal", icon='SHADING_MATERIAL')
        box.prop(scene, "batch_material_library")
        box.prop(scene, "batch_material_name")

        # ── Renderinstellingen ────────────────────────────────────────────
        box = layout.box()
        box.label(text="Renderinstellingen", icon='RENDER_RESULT')
        row = box.row(align=True)
        row.prop(scene, "batch_render_width",  text="B")
        row.prop(scene, "batch_render_height", text="H")
        box.prop(scene, "batch_render_engine", text="Engine")
        if scene.batch_render_engine == 'CYCLES':
            box.prop(scene, "batch_render_samples")

        # ── Output ────────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Output", icon='FOLDER_REDIRECT')
        box.prop(scene, "batch_output_directory")

        # ── Submit ────────────────────────────────────────────────────────
        layout.separator()
        row = layout.row()
        row.scale_y = 2.0
        row.enabled = bool(selected_objs)
        row.operator(
            "wm.batch_marks_to_flamenco",
            text="Verzend naar Flamenco",
            icon='RENDER_ANIMATION',
        )


class VIEW3D_PT_batch_render_marks(bpy.types.Panel):
    """Snel toegangspanel in de 3D Viewport zijbalk"""
    bl_label = "Kleur Verander Objecten"
    bl_idname = "VIEW3D_PT_batch_marks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        selected_count = sum(
            1 for o in scene.objects if o.type == 'MESH' and o.batch_render_selected
        )
        layout.label(
            text=f"Geselecteerd: {selected_count} object(en)",
            icon='OBJECT_DATA',
        )

        box = layout.box()
        _draw_object_list(box, scene)

        layout.separator()
        layout.operator("wm.clear_all_color_objects", text="Alles Wissen", icon='TRASH')


def register():
    bpy.utils.register_class(RENDER_PT_batch_render_marks)
    bpy.utils.register_class(VIEW3D_PT_batch_render_marks)


def unregister():
    bpy.utils.unregister_class(RENDER_PT_batch_render_marks)
    bpy.utils.unregister_class(VIEW3D_PT_batch_render_marks)
