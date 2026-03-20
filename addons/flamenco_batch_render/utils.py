def get_selected_objects(scene):
    """Return all mesh objects marked as color-changing objects."""
    return [obj for obj in scene.objects if obj.type == 'MESH' and obj.batch_render_selected]
