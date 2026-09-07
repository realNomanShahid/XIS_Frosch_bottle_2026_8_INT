"""Load pipeline YAML configs. No hardcoded thresholds in call sites."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def load_all() -> dict[str, dict[str, Any]]:
    return {
        "detection": load_yaml("detection.yaml"),
        "segmentation": load_yaml("segmentation.yaml"),
        "ocr": load_yaml("ocr.yaml"),
        "geometry": load_yaml("geometry.yaml"),
        "tracking": load_yaml("tracking.yaml"),
        "pipeline": load_yaml("pipeline.yaml"),
        "camera": load_yaml("camera.yaml"),
    }