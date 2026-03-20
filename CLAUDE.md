# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This App Does

BlenderTools APP is a macOS desktop application that automates two Blender-related workflows:
1. **Batch Rendering**: Extract mesh objects from `.blend` files, apply materials from a shared material library (`Materialen.blend`), and render each object/material combination as PNG
2. **Image Compression**: Batch-compress images (JPG/PNG) using the embedded Caesium CLI tool

## Running the App

```bash
# Development: activate venv and run
source venv/bin/activate
python3 gui.py

# Or use the provided shell script (handles venv setup automatically)
bash run_gui.sh
```

## Building for Distribution

```bash
# PyInstaller (primary build method)
pyinstaller BlenderTools.spec

# py2app (alternative macOS build)
python setup.py py2app
```

Output goes to `dist/` and `build/`.

## Architecture

### Script Roles

| File | Role |
|------|------|
| `gui.py` | Tkinter GUI — orchestrates all workflows |
| `batch_render.py` | Rendering orchestrator — runs as a subprocess, spawns Blender |
| `render_script.py` | Blender-internal script — runs inside Blender via `bpy`, applies materials and renders |
| `extract_objects.py` | Blender-internal script — extracts mesh object names from a scene |
| `compress.py` | Compression orchestrator — wraps the Caesium CLI |

### Inter-Process Communication

The GUI spawns subprocesses and tracks their progress via **temporary files**:
- `/tmp/render_progress.txt` — current render count
- `/tmp/render_total.txt` — total renders expected
- `/tmp/compression_progress.txt` — compression progress

The GUI polls these files every 100ms on a background thread to update the progress bar.

### Blender Integration

Blender scripts (`render_script.py`, `extract_objects.py`) are executed via Blender's CLI:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background file.blend --python script.py
```

Arguments are passed as `-- arg1 arg2 ...` (everything after `--` is accessible via `sys.argv`).

### Bundled Resources

When running as a PyInstaller bundle, `sys._MEIPASS` is used to locate bundled files (Caesium CLI, Python scripts). In development, paths are relative to the script location.

## Key Constraints

- **macOS only**: Blender path is hardcoded to `/Applications/Blender.app/Contents/MacOS/Blender`
- **Python 3.13** via local `venv/`
- **UI language**: Dutch (labels and user-facing strings are in Dutch)
- The `Materialen.blend` file is the shared material library — all renders apply materials from this file
