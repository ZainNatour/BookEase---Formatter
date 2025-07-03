import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yml"

DEFAULT_CONFIG = {
    "copy_icon_templates": [
        "assets/icons/copy_light.png",
        "assets/icons/copy_dark.png",
    ],
    "chunk_size": 1500,
    "chunk_overlap": 200,
    "typing_indicator_bbox": [1150, 850, 50, 20],
}


def _load_config(path: Path = CONFIG_PATH) -> dict:
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
    else:
        data = {}
    changed = False
    for key, value in DEFAULT_CONFIG.items():
        if key not in data:
            data[key] = value
            changed = True
    if changed:
        try:
            with path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(data, f)
        except Exception:
            pass
    return data


_config = _load_config()
copy_icon_templates = _config["copy_icon_templates"]
chunk_size = _config["chunk_size"]
chunk_overlap = _config["chunk_overlap"]
typing_indicator_bbox = _config["typing_indicator_bbox"]


def get_copy_icons() -> list:
    """Return list of template image paths for the Copy icon."""
    return list(copy_icon_templates)
