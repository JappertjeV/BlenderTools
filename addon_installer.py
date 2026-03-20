import os
import glob
import shutil
import platform
import subprocess
import sys

ADDON_NAME = "flamenco_batch_render"


def get_addon_source():
    """Return path to the bundled addon directory."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "addons", ADDON_NAME)


def _get_blender_version(blender_exe):
    """Return 'major.minor' version string (e.g. '4.2'), or None on failure."""
    try:
        result = subprocess.run(
            [blender_exe, "--version"],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Blender "):
                parts = line.split()
                if len(parts) >= 2:
                    return ".".join(parts[1].split(".")[:2])
    except Exception:
        pass
    return None


def get_addons_dir(blender_exe):
    """
    Return the path to Blender's user add-ons directory, creating it if needed.
    Returns None if it cannot be determined.
    """
    if platform.system() == "Darwin":
        base = os.path.expanduser("~/Library/Application Support/Blender")
    elif platform.system() == "Windows":
        base = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            "Blender Foundation", "Blender",
        )
    else:
        base = os.path.expanduser("~/.config/blender")

    version = _get_blender_version(blender_exe)

    if version:
        addons_dir = os.path.join(base, version, "scripts", "addons")
        os.makedirs(addons_dir, exist_ok=True)
        return addons_dir

    # Fallback: use the highest-versioned existing directory
    matches = sorted(glob.glob(os.path.join(base, "*", "scripts", "addons")), reverse=True)
    if matches:
        return matches[0]

    return None


def is_installed(blender_exe):
    """Return True if the addon folder exists in Blender's add-ons directory."""
    addons_dir = get_addons_dir(blender_exe)
    if not addons_dir:
        return False
    return os.path.isdir(os.path.join(addons_dir, ADDON_NAME))


def install(blender_exe):
    """
    Copy the bundled addon into Blender's add-ons directory.
    Returns (success: bool, message: str).
    """
    source = get_addon_source()
    if not os.path.isdir(source):
        return False, f"Addon bronmap niet gevonden: {source}"

    addons_dir = get_addons_dir(blender_exe)
    if not addons_dir:
        return False, "Blender add-ons map niet gevonden."

    dest = os.path.join(addons_dir, ADDON_NAME)
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        return True, f"Addon geïnstalleerd in:\n{addons_dir}"
    except Exception as e:
        return False, f"Installatie mislukt: {e}"


def uninstall(blender_exe):
    """
    Remove the addon from Blender's add-ons directory.
    Returns (success: bool, message: str).
    """
    addons_dir = get_addons_dir(blender_exe)
    if not addons_dir:
        return False, "Blender add-ons map niet gevonden."

    dest = os.path.join(addons_dir, ADDON_NAME)
    if not os.path.exists(dest):
        return False, "Addon is niet geïnstalleerd."

    try:
        shutil.rmtree(dest)
        return True, "Addon verwijderd."
    except Exception as e:
        return False, f"Verwijdering mislukt: {e}"
