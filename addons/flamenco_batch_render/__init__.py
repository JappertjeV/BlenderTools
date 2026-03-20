bl_info = {
    "name": "Flamenco Batch Renderer",
    "blender": (3, 6, 0),
    "category": "Render",
    "version": (1, 0, 0),
    "author": "Jij",
    "description": "Mark objects as Front/Back and render with different materials via Flamenco",
    "support": "COMMUNITY",
}

import bpy
from . import operators, ui_panels, properties

def register():
    """Register all classes"""
    properties.register()
    operators.register()
    ui_panels.register()
    
    # Context menu
    bpy.types.VIEW3D_MT_object_context_menu.append(operators.add_object_context_menu)
    
    print("✓ Flamenco Batch Renderer loaded")


def unregister():
    """Unregister all classes"""
    # Context menu
    bpy.types.VIEW3D_MT_object_context_menu.remove(operators.add_object_context_menu)
    
    operators.unregister()
    ui_panels.unregister()
    properties.unregister()
    
    print("✗ Flamenco Batch Renderer unloaded")
