"""Config must load and expose required handbook-relevant keys."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REQUIRED_FILES = [
    "detection.yaml",
    "segmentation.yaml",
    "ocr.yaml",
    "geometry.yaml",
    "tracking.yaml",
    "pipeline.yaml",
    "camera.yaml",
]


def _load(configs_dir: Path, name: str) -> dict:
    path = configs_dir / name
    assert path.is_file(), f"Missing config: {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Config must be a mapping: {name}"
    return data


def test_all_config_files_exist(configs_dir: Path):
    for name in REQUIRED_FILES:
        assert (configs_dir / name).is_file(), f"Missing {name}"


def test_geometry_required_keys(configs_dir: Path):
    g = _load(configs_dir, "geometry.yaml")
    for key in (
        "horizontal_center_tolerance",
        "vertical_offset_tolerance",
        "expected_v_offset",
        "spatial_jump_tolerance",
        "history_window",
        "min_history",
    ):
        assert key in g, f"geometry.yaml missing {key}"
    exp = g["expected_v_offset"]
    for cap in (100, 300, 500):
        assert int(cap) in {int(k) for k in exp.keys()} or str(cap) in exp, (
            f"expected_v_offset must include capacity {cap}"
        )


def test_tracking_required_keys(configs_dir: Path):
    t = _load(configs_dir, "tracking.yaml")
    for key in (
        "iou_threshold",
        "max_missing_frames",
        "defect_confirm_streak",
        "defect_overlap_thresh",
        "trigger_line_frac",
    ):
        assert key in t, f"tracking.yaml missing {key}"


def test_detection_class_thresholds(configs_dir: Path):
    d = _load(configs_dir, "detection.yaml")
    assert "class_confidence_thresholds" in d
    thr = d["class_confidence_thresholds"]
    for cls in ("bottle", "label", "capacity", "bump", "damage", "scratch"):
        assert cls in thr, f"Missing threshold for class {cls}"
        assert 0.0 < float(thr[cls]) <= 1.0


def test_load_all_importable(repo_root: Path):
    from src.config import load_all

    cfg = load_all()
    assert set(cfg.keys()) >= {
        "detection",
        "segmentation",
        "ocr",
        "geometry",
        "tracking",
        "pipeline",
        "camera",
    }