"""
Auto-updater for BlenderTools.

Checks GitHub Releases for a newer version and installs it:
  - macOS: downloads a .zip containing the new .app, replaces the current .app
            via a shell script, then relaunches.
  - Windows: downloads the Inno Setup installer and runs it silently.

Only runs when the app is frozen (PyInstaller bundle). In dev mode it just
reports whether an update is available.
"""
import json
import os
import platform
import re
import sys
import tempfile
import urllib.request
import zipfile

from version import GITHUB_REPO, __version__

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


# ── Version comparison ──────────────────────────────────────────────────────

def _parse_version(tag: str) -> tuple:
    tag = tag.lstrip("v")
    parts = re.findall(r"\d+", tag)
    return tuple(int(p) for p in parts)


# ── GitHub API ──────────────────────────────────────────────────────────────

def check_for_update() -> dict | None:
    """Return the latest release dict if newer than current, else None."""
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": f"BlenderTools/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        tag = data.get("tag_name", "")
        if not tag:
            return None

        if _parse_version(tag) > _parse_version(__version__):
            return data
    except Exception:
        pass
    return None


# ── Asset selection ─────────────────────────────────────────────────────────

def _get_asset(release: dict) -> dict | None:
    """Pick the right release asset for the current platform."""
    system = platform.system()
    for asset in release.get("assets", []):
        name = asset["name"].lower()
        if system == "Darwin" and name.endswith(".zip") and "mac" in name:
            return asset
        if system == "Windows" and name.endswith(".exe") and "setup" in name:
            return asset
    return None


# ── Download helper ─────────────────────────────────────────────────────────

def _download(url: str, dest: str, on_progress=None) -> None:
    def _hook(count, block, total):
        if on_progress and total > 0:
            on_progress(min(count * block / total, 1.0))
    urllib.request.urlretrieve(url, dest, _hook)


# ── Platform-specific install ───────────────────────────────────────────────

def _current_app_path() -> str:
    """Resolve the running .app bundle path (macOS) or executable (Windows)."""
    if platform.system() == "Darwin":
        # sys.executable is …/BlenderTools.app/Contents/MacOS/BlenderTools
        app = os.path.normpath(
            os.path.join(os.path.dirname(sys.executable), "..", "..")
        )
        if app.endswith(".app"):
            return app
    return sys.executable


def _install_mac(new_app_src: str, on_status=None) -> bool:
    """Replace the current .app via a background shell script, then relaunch."""
    import subprocess

    current = _current_app_path()
    tmp_dir = os.path.dirname(new_app_src)
    script = (
        "#!/bin/bash\n"
        "sleep 1\n"
        f"rm -rf '{current}'\n"
        f"cp -r '{new_app_src}' '{current}'\n"
        f"open '{current}'\n"
    )
    script_path = os.path.join(tmp_dir, "update.sh")
    with open(script_path, "w") as fh:
        fh.write(script)
    os.chmod(script_path, 0o755)
    subprocess.Popen(["bash", script_path])
    return True


def _install_windows(installer_path: str, on_status=None) -> bool:
    """Run the Inno Setup installer silently."""
    import subprocess
    subprocess.Popen([installer_path, "/SILENT", "/NORESTART"])
    return True


# ── Public entry point ──────────────────────────────────────────────────────

def install_update(
    release: dict,
    on_progress=None,
    on_status=None,
) -> bool:
    """
    Download and install *release*.  Returns True if the install was started
    (the caller should then quit the app so the installer can replace files).
    """
    asset = _get_asset(release)
    if not asset:
        if on_status:
            on_status("Geen download beschikbaar voor dit platform.", "error")
        return False

    tmp_dir = tempfile.mkdtemp(prefix="blendertools_update_")
    dest = os.path.join(tmp_dir, asset["name"])

    try:
        if on_status:
            on_status("Update downloaden...", "info")
        _download(asset["browser_download_url"], dest, on_progress)

        system = platform.system()

        if system == "Darwin":
            if on_status:
                on_status("Update uitpakken...", "info")
            with zipfile.ZipFile(dest, "r") as zf:
                zf.extractall(tmp_dir)

            new_app = next(
                (
                    os.path.join(tmp_dir, f)
                    for f in os.listdir(tmp_dir)
                    if f.endswith(".app")
                ),
                None,
            )
            if not new_app:
                if on_status:
                    on_status("Update mislukt: .app niet gevonden in archief.", "error")
                return False

            if on_status:
                on_status("Update installeren en herstarten...", "info")
            return _install_mac(new_app, on_status)

        elif system == "Windows":
            if on_status:
                on_status("Installatieprogramma starten...", "info")
            return _install_windows(dest, on_status)

    except Exception as exc:
        if on_status:
            on_status(f"Update mislukt: {exc}", "error")

    return False
