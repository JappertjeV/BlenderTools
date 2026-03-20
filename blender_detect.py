import os
import glob
import platform
import sys
from settings import settings


def _get_candidates():
    """Return list of candidate Blender executable paths for the current OS."""
    candidates = []

    if platform.system() == "Darwin":
        candidates += [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
        ]
        candidates += glob.glob("/Applications/Blender*.app/Contents/MacOS/Blender")
        candidates += glob.glob(
            os.path.expanduser("~/Applications/Blender*.app/Contents/MacOS/Blender")
        )

    elif platform.system() == "Windows":
        base_dirs = []
        for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            val = os.environ.get(env)
            if val:
                base_dirs.append(val)

        for base in base_dirs:
            candidates += glob.glob(
                os.path.join(base, "Blender Foundation", "Blender *", "blender.exe")
            )
            candidates += glob.glob(
                os.path.join(base, "Programs", "Blender Foundation", "Blender *", "blender.exe")
            )

        # Check Windows registry
        try:
            import winreg
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    key = winreg.OpenKey(hive, r"SOFTWARE\BlenderFoundation")
                    install_dir, _ = winreg.QueryValueEx(key, "Install_Dir")
                    exe = os.path.join(install_dir, "blender.exe")
                    if exe not in candidates:
                        candidates.append(exe)
                    winreg.CloseKey(key)
                except Exception:
                    pass
        except ImportError:
            pass

    return candidates


def _prompt_picker(parent=None):
    """Show a file picker dialog to locate the Blender executable."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = parent
        if root is None:
            root = tk.Tk()
            root.withdraw()

        if platform.system() == "Windows":
            filetypes = [("Blender executable", "blender.exe"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*")]

        path = filedialog.askopenfilename(
            title="Blender Loceren",
            filetypes=filetypes,
        )
        return path if path else None
    except Exception:
        return None


def find_blender():
    """Return a valid Blender path or None (no dialog)."""
    saved = settings.get("blender_path")
    if saved and os.path.isfile(saved):
        return saved

    for path in _get_candidates():
        if os.path.isfile(path) and os.access(path, os.X_OK):
            settings.set("blender_path", path)
            return path

    return None


def require_blender(parent=None) -> str:
    """Return a valid Blender path or raise RuntimeError."""
    path = find_blender()
    if path:
        return path

    # Prompt user
    path = _prompt_picker(parent)
    if path and os.path.isfile(path) and os.access(path, os.X_OK):
        settings.set("blender_path", path)
        return path

    raise RuntimeError(
        "Blender niet gevonden. Installeer Blender of stel het pad in via Instellingen."
    )
