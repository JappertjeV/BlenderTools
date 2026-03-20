"""
Utility functions for Flamenco Batch Renderer
"""

def get_marked_objects(scene):
    """Get all marked objects in scene"""
    front = [obj for obj in scene.objects if obj.batch_render_type == 'FRONT']
    back = [obj for obj in scene.objects if obj.batch_render_type == 'BACK']
    return front, back
