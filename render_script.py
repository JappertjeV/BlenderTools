import bpy
import os
import sys
import time  # Toegevoegde import
import tempfile

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS  # Gebundelde modus
else:
    base_dir = os.path.dirname(__file__)  # Development modus

# 📌 Bestandsnaam en pad ophalen
try:
    filepath = bpy.data.filepath
    filename = os.path.basename(filepath)
    filename_no_ext = os.path.splitext(filename)[0]
except Exception as e:
    print(f"Fout bij het ophalen van bestandsinformatie: {e}")
    sys.exit(1)

# 📁 Output-map instellen (submap per .blend-bestand)
output_dir = sys.argv[-1]  # Hoofdmap van GUI
output_subdir = os.path.join(output_dir, filename_no_ext)

try:
    os.makedirs(output_subdir, exist_ok=True)
except Exception as e:
    print(f"Fout bij het aanmaken van de outputmap: {e}")
    sys.exit(1)

# Log de output directory
print(f"Output directory: {output_subdir}")

# 📂 Pad naar het Blender-bestand met materialen
source_blend = os.path.join(base_dir, "Materialen.blend")

# 📂 Geselecteerde objecten ophalen (laatste argument is output_dir)
try:
    selected_objects_str = sys.argv[sys.argv.index("--") + 1:-1]
except Exception as e:
    print(f"Fout bij het ophalen van geselecteerde objecten: {e}")
    sys.exit(1)

print("Geselecteerde objecten:", selected_objects_str)

# 📥 Importeer ALLE materialen uit het externe bestand
try:
    original_materials = set(bpy.data.materials.keys())  # Materialen vóór import
    with bpy.data.libraries.load(source_blend, link=False) as (data_from, data_to):
        data_to.materials = data_from.materials
except Exception as e:
    print(f"Fout bij het importeren van materialen: {e}")
    sys.exit(1)

# 🎯 Filter GEÏMPORTEERDE materialen
imported_materials = [
    mat for mat in bpy.data.materials 
    if mat.name not in original_materials
]

# Log de geïmporteerde materialen
print(f"Gevonden materialen: {imported_materials}")

# 🎥 Renderinstellingen toepassen
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 0

# 🔍 Zoek objecten op basis van geselecteerde namen
def find_objects_by_selection(selected_objects_str):
    found_objects = []
    current_filename = os.path.basename(bpy.data.filepath)
    
    for selected_obj_str in selected_objects_str:
        # Parse the format "filename: objectname"
        if ":" in selected_obj_str:
            file_part, obj_name = selected_obj_str.split(":", 1)
            file_part = file_part.strip()
            obj_name = obj_name.strip()
            
            # Check if this object belongs to the current file
            if file_part == current_filename:
                # Find the object in the scene
                if obj_name in bpy.context.scene.objects:
                    obj = bpy.context.scene.objects[obj_name]
                    if obj.type == 'MESH':
                        found_objects.append(obj)
                        print(f"✅ Gevonden object: {obj.name}")
        else:
            # Fallback: direct object name (for backward compatibility)
            if selected_obj_str in bpy.context.scene.objects:
                obj = bpy.context.scene.objects[selected_obj_str]
                if obj.type == 'MESH':
                    found_objects.append(obj)
                    print(f"✅ Gevonden object: {obj.name}")
    
    return found_objects

# 🧹 Verwijder alle materialen van de objecten
def clear_materials(objects):
    for obj in objects:
        obj.data.materials.clear()
    print(f"🗑️ Alle materialen verwijderd van {len(objects)} object(en).")

# 🎨 Render alle objecten met elk materiaal
def render_with_material(material, output_path, objects):
    if not objects:
        print("⚠️ Geen objecten om te renderen!")
        return

    # Verwijder bestaande materialen en voeg het huidige materiaal toe
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)

    print(f"🎨 Toegepast materiaal: {material.name} op {len(objects)} objecten.")
    
    # Render opslaan
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    
    # Update voortgang (1 regel per gerenderd materiaal)
    with open(os.path.join(tempfile.gettempdir(), "render_progress.txt"), "a") as f:
        f.write("1\n")

# Zoek objecten met de geselecteerde objecten
objects_to_process = find_objects_by_selection(selected_objects_str)

if objects_to_process:
    # 🧹 Verwijder eerst alle materialen
    clear_materials(objects_to_process)

    # Render ALLEEN geïmporteerde materialen
    for material in imported_materials:
        output_path = os.path.join(output_subdir, f"{filename_no_ext}_{material.name}.png")
        render_with_material(material, output_path, objects_to_process)

    print("🎉 Materialen uit Materialen.blend gerenderd!")
else:
    print("⚠️ Geen objecten gevonden met de opgegeven naam!")