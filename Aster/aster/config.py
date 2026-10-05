"""Validated preferences and writable per-user locations."""
from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json
import os

SCENES = ("galaxy", "nebula", "system")
QUALITY = {"low": 0.35, "medium": 0.7, "high": 1.0, "ultra": 2.0}


@dataclass
class Settings:
    scene: str = "galaxy"
    seed: int = 42
    quality: str = "high"
    exposure: float = 1.1
    bloom: float = 0.65
    size: float = 1.0
    density: float = 1.0
    speed: float = 12.0
    motion: bool = True
    palette: int = 0

    def validate(self):
        if self.scene not in SCENES:
            self.scene = "galaxy"
        if self.quality not in QUALITY:
            self.quality = "high"
        self.seed = max(0, min(2**32 - 1, int(self.seed)))
        self.palette = int(self.palette) % 3
        for name, low, high in (("exposure", 0.3, 2.5), ("bloom", 0.0, 1.5),
                                ("size", 0.4, 2.0), ("density", 0.15, 1.0),
                                ("speed", 0.2, 250.0)):
            value = float(getattr(self, name))
            if not low <= value <= high:  # also rejects NaN
                value = getattr(Settings(), name)
            setattr(self, name, value)
        self.motion = bool(self.motion)
        return self


def data_dir():
    root = os.environ.get("ASTER_DATA_DIR")
    path = Path(root) if root else Path.home() / ".aster"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_settings(path=None):
    path = Path(path) if path else data_dir() / "settings.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        names = {field.name for field in fields(Settings)}
        return Settings(**{k: v for k, v in payload.items() if k in names}).validate()
    except (OSError, ValueError, TypeError, AttributeError, OverflowError):
        return Settings()


def save_settings(settings, path=None):
    path = Path(path) if path else data_dir() / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(settings.validate()), indent=2), encoding="utf-8")
    temporary.replace(path)
