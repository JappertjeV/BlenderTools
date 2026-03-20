import bpy
import os
import sys
import json
import tempfile


def extract_mesh_objects():
    """Extract all mesh object names from the currently loaded Blender file."""
    try:
        return [obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH']
    except Exception as e:
        print(f"Error extracting objects: {e}")
        return []


def extract_batch_marks():
    """
    Read color-changing object selections stored by the flamenco_batch_render addon.
    Falls back to reading object-level custom properties when the addon is absent.
    Returns {"selected": [...]}
    """
    scene = bpy.context.scene

    # Primary: plain JSON custom property written by the addon after each selection change
    marks_json = scene.get("batch_render_marks")
    if marks_json:
        try:
            data = json.loads(marks_json)
            return {
                "selected": [n for n in data.get("selected", []) if isinstance(n, str)],
            }
        except Exception:
            pass

    # Fallback: individual object custom properties
    selected = [
        obj.name for obj in scene.objects
        if obj.type == 'MESH' and obj.get("batch_render_selected")
    ]
    return {"selected": selected}


def main():
    current_file = bpy.data.filepath
    filename = os.path.basename(current_file) if current_file else "unknown"

    objects = extract_mesh_objects()
    marks   = extract_batch_marks()

    # Write objects to temp file (legacy — kept for backward compat)
    temp_file = os.path.join(tempfile.gettempdir(), f"objects_{filename}.txt")
    with open(temp_file, 'w') as f:
        for obj in objects:
            f.write(f"{obj}\n")

    print(f"Extracted {len(objects)} objects from {filename}")
    print(f"Objects saved to: {temp_file}")

    # Print each object name (parsed by GUI)
    for obj in objects:
        print(obj)

    # Print marks as a single parseable line (parsed by GUI)
    print(f"BATCH_MARKS:{json.dumps(marks)}")


if __name__ == "__main__":
    main()
