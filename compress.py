import argparse
import os
import subprocess
import sys
from tqdm import tqdm

import platform
import shutil


def _get_caesium_path():
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    if platform.system() == "Darwin":
        return os.path.join(base, "bin", "mac", "caesiumclt")
    elif platform.system() == "Windows":
        return os.path.join(base, "bin", "win", "caesiumclt.exe")
    else:
        return shutil.which("caesiumclt") or os.path.join(base, "bin", "linux", "caesiumclt")


caesium_path = _get_caesium_path()

def compress_images(input_paths, output_dir, max_size_kb, progress_file=None):
    # Verzamel alle bestanden
    all_inputs = []
    for path in input_paths:
        if os.path.isdir(path):
            base_path = path
            for root, _, files in os.walk(path):
                for f in files:
                    if f.lower().endswith((".jpg", ".jpeg", ".png")):
                        all_inputs.append((os.path.join(root, f), base_path))
        else:
            all_inputs.append((path, os.path.dirname(path)))

    # Zorg dat de output map bestaat
    os.makedirs(output_dir, exist_ok=True)

    # Reset voortgangsbestand
    if progress_file:
        with open(progress_file, "w") as f:
            f.write("")  # Begin met een leeg bestand

    # Compressie uitvoeren met voortgangsbalk
    with tqdm(total=len(all_inputs), desc="Comprimeren") as pbar:
        for i, (input_path, base_path) in enumerate(all_inputs):
            rel_path = os.path.relpath(input_path, base_path)
            output_subdir = os.path.join(output_dir, os.path.dirname(rel_path))
            os.makedirs(output_subdir, exist_ok=True)
            
            pbar.set_description(f"Comprimeren: {os.path.basename(input_path)}")
            
            try:
                subprocess.run([
                    caesium_path,
                    "--max-size", str(max_size_kb * 1024),
                    "-o", output_subdir,
                    input_path
                ], check=True)
                
                # Update voortgang
                if progress_file:
                    with open(progress_file, "a") as f:  # Gebruik append mode
                        f.write("1\n")  # Voeg één regel toe per verwerkt bestand
                pbar.update(1)
                
            except subprocess.CalledProcessError as e:
                print(f"\nFout bij comprimeren van {rel_path}: {e}")
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-size", type=int, default=300)
    parser.add_argument("--progress-file", type=str)
    args = parser.parse_args()
    
    compress_images(args.input.split(","), args.output, args.max_size, args.progress_file)