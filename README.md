# BlenderTools

A macOS and Windows desktop app for automating Blender batch rendering and image compression.

## Features

- **Batch Rendering** — select `.blend` files, pick mesh objects and materials, render every combination as PNG
- **Image Compression** — batch-compress JPG/PNG files using the bundled Caesium CLI
- **Auto-updater** — checks GitHub Releases on startup and installs updates automatically

## Requirements

- Python 3.13
- [Blender](https://www.blender.org/download/) installed on your system
- macOS 10.13+ or Windows 10 64-bit

## Running in Development

```bash
# Clone the repo
git clone https://github.com/JappertjeV/BlenderTools.git
cd BlenderTools

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python gui.py
```

## Building for Distribution

### macOS (.app bundle)

```bash
pyinstaller BlenderTools.spec
# Output: dist/BlenderTools.app
```

### Windows (.exe)

```bash
pyinstaller BlenderTools.spec
# Output: dist/BlenderTools.exe
```

Then build the installer with [Inno Setup 6](https://jrsoftware.org/isinfo.php):

```
installer/BlenderTools.iss
# Output: dist/installer/BlenderTools-Setup-0.x.x.exe
```

## Project Structure

| File | Description |
|------|-------------|
| `gui.py` | Main CustomTkinter GUI |
| `batch_render.py` | Rendering orchestrator (subprocess) |
| `render_script.py` | Blender-internal render script (runs via `bpy`) |
| `extract_objects.py` | Blender-internal object extractor |
| `compress.py` | Image compression wrapper around Caesium CLI |
| `settings.py` | Persistent JSON settings |
| `blender_detect.py` | Auto-detects Blender on macOS and Windows |
| `version.py` | Version number and GitHub repo reference |
| `updater.py` | GitHub Releases auto-updater |
| `Materialen.blend` | Shared material library used during rendering |
| `bin/mac/caesiumclt` | Caesium CLI binary (macOS) |
| `bin/win/caesiumclt.exe` | Caesium CLI binary (Windows) |
| `installer/BlenderTools.iss` | Inno Setup 6 installer script (Windows) |

## Releasing an Update

1. Bump `__version__` in `version.py` (e.g. `0.2.0` → `0.2.1`)
2. Update the version in `installer/BlenderTools.iss`
3. Build the app for each platform
4. Create a GitHub Release with tag `v0.2.1` and attach:
   - `BlenderTools-0.2.1-mac.zip` — zip of `BlenderTools.app`
   - `BlenderTools-Setup-0.2.1.exe` — Inno Setup output

The auto-updater picks up the new release on next startup and installs it.

## Versioning

This project uses [0ver](https://0ver.org) — the major version is always `0`.

## License

MIT
