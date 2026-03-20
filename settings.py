from pathlib import Path
import os
import json
import platform


def get_config_dir() -> Path:
    if platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    elif platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".config"
    d = base / "BlenderTools"
    d.mkdir(parents=True, exist_ok=True)
    return d


DEFAULTS = {
    "blender_path": "",
    "last_blend_dir": "",
    "last_output_dir": "",
    "last_compress_input": "",
    "last_compress_output": "",
    "max_file_size_kb": 300,
    "appearance_mode": "dark",
    "flamenco_manager_url": "http://localhost:8080",
    "flamenco_front_material": "front_material",
    "flamenco_back_material": "back_material",
    "flamenco_material_library": "",
}


class Settings:
    def __init__(self):
        self._path = get_config_dir() / "settings.json"
        self._data = {**DEFAULTS}
        self.load()

    def load(self):
        if self._path.exists():
            try:
                self._data.update(json.loads(self._path.read_text()))
            except Exception:
                pass

    def save(self):
        self._path.write_text(json.dumps(self._data, indent=2))

    def get(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()


settings = Settings()
