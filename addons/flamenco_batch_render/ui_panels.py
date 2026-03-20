import bpy


class RENDER_PT_batch_render_marks(bpy.types.Panel):
    """Panel for managing batch render marks"""
    bl_label = "Batch Render Marks"
    bl_idname = "RENDER_PT_batch_marks"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Instructions
        box = layout.box()
        box.label(text="How to use:", icon='INFO')
        col = box.column(align=True)
        col.scale_y = 0.9
        col.label(text="1. Right-click object in viewport")
        col.label(text="2. Select 'Mark as Front' or 'Mark as Back'")
        col.label(text="3. Configure settings below")
        col.label(text="4. Click 'Submit to Flamenco'")
        
        # Flamenco connection
        box = layout.box()
        box.label(text="Flamenco Manager", icon='NETWORK_DRIVE')
        box.prop(scene, "flamenco_manager_url")
        box.prop(scene, "batch_open_ui_after_submit")
        
        # Materials
        box = layout.box()
        box.label(text="Materials", icon='SHADING_MATERIAL')
        box.prop(scene, "batch_material_library")
        
        row = box.row(align=True)
        row.prop(scene, "batch_front_material", text="Front")
        row.prop(scene, "batch_back_material", text="Back")
        
        # Render settings
        box = layout.box()
        box.label(text="Render Settings", icon='RENDER_RESULT')
        
        row = box.row(align=True)
        row.prop(scene, "batch_render_width", text="W")
        row.prop(scene, "batch_render_height", text="H")
        
        row = box.row(align=True)
        row.prop(scene, "batch_render_engine", text="Engine")
        
        if scene.batch_render_engine == 'CYCLES':
            row = box.row()
            row.prop(scene, "batch_render_samples")
        
        # Output directory
        box = layout.box()
        box.label(text="Output", icon='FOLDER_REDIRECT')
        box.prop(scene, "batch_output_directory")
        
        # Marked objects summary
        front_objs = [obj for obj in scene.objects if obj.batch_render_type == 'FRONT']
        back_objs = [obj for obj in scene.objects if obj.batch_render_type == 'BACK']
        
        box = layout.box()
        box.label(text=f"Marked Objects: {len(front_objs) + len(back_objs)}", icon='OBJECT_DATA')
        
        if front_objs:
            col = box.column(align=True)
            col.label(text=f"Front (🔴 Red): {len(front_objs)}", icon='CIRCLE')
            for obj in front_objs:
                row = col.row(align=True)
                row.label(text=f"  • {obj.name}")
                row.operator("wm.unmark_object", text="", icon='X').object_name = obj.name
        
        if back_objs:
            col = box.column(align=True)
            col.label(text=f"Back (🔵 Blue): {len(back_objs)}", icon='CIRCLE')
            for obj in back_objs:
                row = col.row(align=True)
                row.label(text=f"  • {obj.name}")
                row.operator("wm.unmark_object", text="", icon='X').object_name = obj.name
        
        if not front_objs and not back_objs:
            box.label(text="No objects marked yet", icon='INFO')
        
        # Actions
        layout.separator()
        
        row = layout.row(align=True)
        row.operator("wm.clear_all_marks", text="Clear All Marks", icon='TRASH')
        
        # Submit button (only if objects marked)
        if front_objs or back_objs:
            row = layout.row()
            row.scale_y = 2.0
            row.operator("wm.batch_marks_to_flamenco", text="Submit to Flamenco", icon='RENDER_ANIMATION')
        else:
            row = layout.row()
            row.enabled = False
            row.scale_y = 2.0
            row.operator("wm.batch_marks_to_flamenco", text="Submit to Flamenco (Mark objects first)", icon='RENDER_ANIMATION')


class VIEW3D_PT_batch_render_marks(bpy.types.Panel):
    """Panel in 3D viewport for quick access"""
    bl_label = "Batch Render"
    bl_idname = "VIEW3D_PT_batch_marks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        
        # Object status
        if obj:
            box = layout.box()
            box.label(text=f"Active: {obj.name}", icon='OBJECT_DATA')
            
            row = box.row(align=True)
            row.scale_y = 1.2
            
            if obj.batch_render_type == 'FRONT':
                row.operator("wm.mark_object_front", text="Front", icon='CHECKMARK', depress=True)
            else:
                row.operator("wm.mark_object_front", text="Front")
            
            if obj.batch_render_type == 'BACK':
                row.operator("wm.mark_object_back", text="Back", icon='CHECKMARK', depress=True)
            else:
                row.operator("wm.mark_object_back", text="Back")
            
            if obj.batch_render_type != 'NONE':
                row.operator("wm.unmark_object", text="Unmark", icon='X')
        else:
            layout.label(text="Select an object", icon='INFO')
        
        # Quick summary
        layout.separator()
        front_objs = len([o for o in scene.objects if o.batch_render_type == 'FRONT'])
        back_objs = len([o for o in scene.objects if o.batch_render_type == 'BACK'])
        
        row = layout.row()
        row.label(text=f"🔴 Front: {front_objs}")
        row.label(text=f"🔵 Back: {back_objs}")
        
        if front_objs + back_objs > 0:
            layout.operator("wm.clear_all_marks", text="Clear Marks", icon='TRASH')


def register():
    """Register UI panels"""
    bpy.utils.register_class(RENDER_PT_batch_render_marks)
    bpy.utils.register_class(VIEW3D_PT_batch_render_marks)


def unregister():
    """Unregister UI panels"""
    bpy.utils.unregister_class(RENDER_PT_batch_render_marks)
    bpy.utils.unregister_class(VIEW3D_PT_batch_render_marks)
