import bpy
from bpy.props import StringProperty, EnumProperty


def register():
    """Register properties"""
    
    # Object marking
    bpy.types.Object.batch_render_type = EnumProperty(
        name="Batch Render Type",
        description="Mark object for batch rendering",
        items=[
            ('NONE', "None", "Not marked for batch render", 'CIRCLE', 0),
            ('FRONT', "Front Color", "Will get front material (Red)", 'CIRCLE', 1),
            ('BACK', "Back Color", "Will get back material (Blue)", 'CIRCLE', 2),
        ],
        default='NONE'
    )
    
    # Scene properties
    bpy.types.Scene.flamenco_manager_url = StringProperty(
        name="Manager URL",
        description="Flamenco Manager URL (e.g., http://localhost:8080)",
        default="http://localhost:8080"
    )
    
    bpy.types.Scene.batch_material_library = StringProperty(
        name="Material Library",
        description="Path to .blend file with materials",
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.batch_front_material = StringProperty(
        name="Front Material Name",
        description="Material name for front color objects",
        default="front_material"
    )
    
    bpy.types.Scene.batch_back_material = StringProperty(
        name="Back Material Name",
        description="Material name for back color objects",
        default="back_material"
    )
    
    bpy.types.Scene.batch_output_directory = StringProperty(
        name="Output Directory",
        description="Where to save rendered images",
        subtype='DIR_PATH'
    )
    
    bpy.types.Scene.batch_render_width = bpy.props.IntProperty(
        name="Width",
        description="Render width in pixels",
        default=1280,
        min=64,
        max=16384
    )
    
    bpy.types.Scene.batch_render_height = bpy.props.IntProperty(
        name="Height",
        description="Render height in pixels",
        default=720,
        min=64,
        max=16384
    )
    
    bpy.types.Scene.batch_render_samples = bpy.props.IntProperty(
        name="Samples",
        description="Cycles render samples",
        default=128,
        min=1,
        max=10000
    )
    
    bpy.types.Scene.batch_render_engine = EnumProperty(
        name="Render Engine",
        items=[
            ('CYCLES', "Cycles", "Cycles render engine"),
            ('EEVEE', "EEVEE", "EEVEE render engine"),
        ],
        default='CYCLES'
    )
    
    bpy.types.Scene.batch_open_ui_after_submit = bpy.props.BoolProperty(
        name="Open UI After Submit",
        description="Automatically open Flamenco UI in browser",
        default=True
    )


def unregister():
    """Unregister properties"""
    if hasattr(bpy.types.Object, 'batch_render_type'):
        del bpy.types.Object.batch_render_type
    
    # Scene properties
    props = [
        'flamenco_manager_url',
        'batch_material_library',
        'batch_front_material',
        'batch_back_material',
        'batch_output_directory',
        'batch_render_width',
        'batch_render_height',
        'batch_render_samples',
        'batch_render_engine',
        'batch_open_ui_after_submit',
    ]
    
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
