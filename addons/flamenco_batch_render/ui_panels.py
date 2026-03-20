import bpy


def _draw_object_list(layout, scene):
    """Draw a selectable list of all mesh objects with Front/Back toggle buttons."""
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
        is_front = obj.batch_render_type == 'FRONT'
        is_back  = obj.batch_render_type == 'BACK'

        # Front button — active (pressed) when marked FRONT
        op = row.operator("wm.mark_object_front", text="F", depress=is_front)
        op.object_name = obj.name

        # Back button — active (pressed) when marked BACK
        op = row.operator("wm.mark_object_back", text="B", depress=is_back)
        op.object_name = obj.name

        # Object name — align left
        row.label(text=obj.name)

        # Remove button — only if currently marked
        if obj.batch_render_type != 'NONE':
            row.operator("wm.unmark_object", text="", icon='X').object_name = obj.name


class RENDER_PT_batch_render_marks(bpy.types.Panel):
    """Main configuration panel in Properties → Output"""
    bl_label = "Batch Render Marks"
    bl_idname = "RENDER_PT_batch_marks"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Object selectie ────────────────────────────────────────────────
        box = layout.box()
        front_objs = [o for o in scene.objects if o.type == 'MESH' and o.batch_render_type == 'FRONT']
        back_objs  = [o for o in scene.objects if o.type == 'MESH' and o.batch_render_type == 'BACK']

        row = box.row()
        row.label(text=f"Objecten  —  Front: {len(front_objs)}   Back: {len(back_objs)}", icon='OBJECT_DATA')

        _draw_object_list(box, scene)

        row = box.row()
        row.operator("wm.clear_all_marks", text="Alles Wissen", icon='TRASH')

        # ── Flamenco verbinding ────────────────────────────────────────────
        box = layout.box()
        box.label(text="Flamenco Manager", icon='NETWORK_DRIVE')
        box.prop(scene, "flamenco_manager_url")
        box.prop(scene, "batch_open_ui_after_submit")

        # ── Materialen ────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Materialen", icon='SHADING_MATERIAL')
        box.prop(scene, "batch_material_library")
        row = box.row(align=True)
        row.prop(scene, "batch_front_material", text="Front")
        row.prop(scene, "batch_back_material",  text="Back")

        # ── Renderinstellingen ────────────────────────────────────────────
        box = layout.box()
        box.label(text="Renderinstellingen", icon='RENDER_RESULT')
        row = box.row(align=True)
        row.prop(scene, "batch_render_width",  text="B")
        row.prop(scene, "batch_render_height", text="H")
        row = box.row(align=True)
        row.prop(scene, "batch_render_engine", text="Engine")
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
        row.enabled = bool(front_objs or back_objs)
        row.operator("wm.batch_marks_to_flamenco", text="Verzend naar Flamenco", icon='RENDER_ANIMATION')


class VIEW3D_PT_batch_render_marks(bpy.types.Panel):
    """Quick-access panel in the 3D Viewport side bar"""
    bl_label = "Batch Render"
    bl_idname = "VIEW3D_PT_batch_marks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Samenvatting ──────────────────────────────────────────────────
        front_count = sum(1 for o in scene.objects if o.type == 'MESH' and o.batch_render_type == 'FRONT')
        back_count  = sum(1 for o in scene.objects if o.type == 'MESH' and o.batch_render_type == 'BACK')

        row = layout.row()
        row.label(text=f"Front: {front_count}", icon='SEQUENCE_COLOR_01')
        row.label(text=f"Back: {back_count}",   icon='SEQUENCE_COLOR_05')

        # ── Object lijst ──────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Kleur veranderende objecten", icon='OBJECT_DATA')
        _draw_object_list(box, scene)

        # ── Acties ────────────────────────────────────────────────────────
        layout.separator()
        layout.operator("wm.clear_all_marks", text="Alles Wissen", icon='TRASH')


def register():
    bpy.utils.register_class(RENDER_PT_batch_render_marks)
    bpy.utils.register_class(VIEW3D_PT_batch_render_marks)


def unregister():
    bpy.utils.unregister_class(RENDER_PT_batch_render_marks)
    bpy.utils.unregister_class(VIEW3D_PT_batch_render_marks)
