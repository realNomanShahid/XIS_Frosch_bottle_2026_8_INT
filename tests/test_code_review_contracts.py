"""Static contracts: config usage, no silent fallbacks in production path."""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


def _read(src_dir: Path, name: str) -> str:
    path = src_dir / name
    assert path.is_file(), f"Missing source file: {path}"
    return path.read_text(encoding="utf-8", errors="replace")


def test_live_inference_loads_config(src_dir: Path):
    text = _read(src_dir, "live_inference.py")
    assert "load_all" in text or "from src.config import" in text
    assert "CFG" in text or "load_all(" in text


def test_no_hardcoded_expected_v_block_left(src_dir: Path):
    """Old CAP_TYPE_A/B/C constants should not remain as the source of truth."""
    text = _read(src_dir, "live_inference.py")
    # Allow comments; forbid assignment of the old constants as primary config
    assert "CAP_TYPE_A_EXPECTED_V_OFFSET =" not in text
    assert "CAP_TYPE_B_EXPECTED_V_OFFSET =" not in text
    assert "CAP_TYPE_C_EXPECTED_V_OFFSET =" not in text


def test_live_inference_has_no_bare_except_pass(src_dir: Path):
    """Broad except: pass that swallows errors is a handbook risk."""
    text = _read(src_dir, "live_inference.py")
    # crude but useful guard
    assert re.search(r"except\s*:\s*\n\s*pass", text) is None


def test_inference_module_exists(src_dir: Path):
    assert (src_dir / "inference.py").is_file()
    assert (src_dir / "config.py").is_file()


def test_query_gpu_stats_returns_zeros_on_failure(src_dir: Path):
    """Failure path must return explicit zeros, not a previous fake reading."""
    text = _read(src_dir, "live_inference.py")
    assert "return 0, 0, 0" in text or "return 0,0,0" in text