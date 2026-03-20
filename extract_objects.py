import bpy
import os
import sys
import tempfile

def extract_mesh_objects():
    """Extract all mesh object names from the currently loaded Blender file"""
    try:
        # Get all mesh objects from the current scene
        mesh_objects = []
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                mesh_objects.append(obj.name)
        
        return mesh_objects
        
    except Exception as e:
        print(f"Error extracting objects: {e}")
        return []

def main():
    # Extract objects from the currently loaded file
    objects = extract_mesh_objects()
    
    # Get the current file name for logging
    current_file = bpy.data.filepath
    if current_file:
        filename = os.path.basename(current_file)
    else:
        filename = "unknown"
    
    # Write to temporary file
    temp_file = os.path.join(tempfile.gettempdir(), f"objects_{filename}.txt")
    with open(temp_file, 'w') as f:
        for obj in objects:
            f.write(f"{obj}\n")
    
    print(f"Extracted {len(objects)} objects from {filename}")
    print(f"Objects saved to: {temp_file}")
    
    # Also print to stdout for direct access
    for obj in objects:
        print(obj)

if __name__ == "__main__":
    main()
