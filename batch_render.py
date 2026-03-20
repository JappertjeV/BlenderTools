import sys
import os
import subprocess
from tqdm import tqdm
import tempfile

# Command-line argumenten splitsen
try:
    blend_files = sys.argv[1:-2]      # .blend-bestanden
    selected_objects_str = sys.argv[-2]  # Geselecteerde objecten (pipe-separated)
    output_dir = sys.argv[-1]           # Output-map
except IndexError:
    print("Fout: Niet genoeg argumenten opgegeven.")
    sys.exit(1)

# Blender executable — resolved at runtime via settings/detection
try:
    from blender_detect import require_blender
    blender_exe = require_blender()
except Exception as e:
    print(f"Fout: Blender niet gevonden — {e}")
    sys.exit(1)

# Log de ontvangen argumenten
print(f"Blend files: {blend_files}")
print(f"Selected objects: {selected_objects_str}")
print(f"Output directory: {output_dir}")

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(__file__)
render_script = os.path.join(base_dir, "render_script.py")

# Zorg dat de output map bestaat
try:
    os.makedirs(output_dir, exist_ok=True)
except Exception as e:
    print(f"Fout bij het aanmaken van de uitvoermap: {e}")
    sys.exit(1)

# Reset en maak een nieuw bestand voor het totale aantal materialen
total_materials_file = os.path.join(tempfile.gettempdir(), "total_materials.txt")
try:
    open(total_materials_file, "w").close()
except Exception as e:
    print(f"Fout bij het resetten van het totale materialenbestand: {e}")
    sys.exit(1)

# Verwerk geselecteerde objecten
if isinstance(selected_objects_str, str):
    selected_objects = selected_objects_str.split("|")
else:
    selected_objects = []

# Hoofdloop voor renderen
for i, blend_file in enumerate(blend_files):
    print(f"🎬 Rendering {blend_file}...")
    
    # Renderproces voor dit bestand
    try:
        blender_command = [
            blender_exe,
            "--background",  # Zonder GUI
            "--factory-startup",  # Negeer gebruikersinstellingen
            "--enable-autoexec",  # Toch Python scripts laden
            blend_file,
            "--python", render_script,
            "--",
            *selected_objects,
            output_dir
        ]

        # Voor macOS specifiek
        if sys.platform == "darwin":
            blender_command.insert(1, "--disable-crash-handler")

        result = subprocess.run(blender_command, check=True)

        print(f"Render result: {result}")
    except subprocess.CalledProcessError as e:
        print(f"Fout bij het uitvoeren van de render: {e}")
        continue
    except Exception as e:
        print(f"Onverwachte fout tijdens renderen: {e}")
        continue

    # Voorspel het aantal materialen
    try:
        subprocess.run([
            blender_exe,
            blend_file,
            "--background",
            "--python", render_script,
            "--",
            "GET_MATERIAL_COUNT",  # Speciale vlag
            output_dir
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Fout bij het ophalen van het aantal materialen: {e}")
        continue
    except Exception as e:
        print(f"Onverwachte fout tijdens het ophalen van het aantal materialen: {e}")
        continue
    
    # Lees het aantal materialen uit een tijdelijk bestand
    material_count_file = os.path.join(tempfile.gettempdir(), "material_count.txt")
    try:
        with open(material_count_file, "r") as f:
            material_count = int(f.read().strip())

        # Update totaal
        with open(total_materials_file, "a") as f:
            f.write(f"{material_count}\n")
    except FileNotFoundError:
        print("Fout: Het tijdelijke bestand voor het aantal materialen is niet gevonden.")
    except ValueError:
        print("Fout: Ongeldig aantal materialen gelezen.")
    except Exception as e:
        print(f"Fout bij het bijwerken van het totale aantal materialen: {e}")
    
    print(f"✅ Render voltooid voor bestand: {blend_file}")

print("🎉 Alle renders voltooid!")