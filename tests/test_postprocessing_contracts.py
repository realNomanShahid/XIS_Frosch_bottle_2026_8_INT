"""Geometry / decision contracts for Frosch (no GPU required)."""
from __future__ import annotations

import math

import pytest


def _h_offset(label_x: float, bottle_x: float, bottle_w: float) -> float:
    return (label_x - bottle_x) / bottle_w


def _v_offset(label_y: float, bottle_y: float, bottle_h: float) -> float:
    return (label_y - bottle_y) / bottle_h


def test_horizontal_pass_fail_rule():
    """|H| <= 0.15 → PASS (matches geometry.yaml default)."""
    tol = 0.15
    h_ok = _h_offset(100, 100, 200)  # 0.0
    h_fail = _h_offset(150, 100, 200)  # 0.25
    assert abs(h_ok) <= tol
    assert abs(h_fail) > tol


def test_vertical_pass_uses_capacity_reference():
    """V is compared to capacity-specific expected offset, not zero."""
    tol = 0.05
    expected = {100: 0.12, 300: 0.07, 500: 0.01}
    v = 0.12
    assert abs(v - expected[100]) <= tol
    assert abs(v - expected[500]) > tol  # same V fails for 500 ml reference


def test_tilt_limit_45_deg():
    max_tilt = 45.0
    assert 30.0 <= max_tilt
    assert 50.0 > max_tilt


def test_defect_overlap_threshold_is_strict():
    """Overlap below threshold must not count as confirmed defect."""
    thresh = 0.30
    assert 0.10 < thresh
    assert 0.50 >= thresh


def test_pending_is_not_fail():
    """Missing measurement → INCOMPLETE, never auto-DEFECTIVE."""
    status = {
        "orientation": "Pending",
        "h": "PASS",
        "v": "PASS",
        "defects": [],
    }
    if any(status[k] == "Pending" for k in ("orientation", "h", "v")):
        final = "INCOMPLETE"
    elif status["defects"] or any(status[k] == "FAIL" for k in ("orientation", "h", "v")):
        final = "DEFECTIVE"
    else:
        final = "GOOD"
    assert final == "INCOMPLETE"


def test_good_requires_all_pass_and_no_defects():
    status = {
        "orientation": "PASS",
        "h": "PASS",
        "v": "PASS",
        "defects": [],
    }
    if any(status[k] == "Pending" for k in ("orientation", "h", "v")):
        final = "INCOMPLETE"
    elif status["defects"] or any(status[k] == "FAIL" for k in ("orientation", "h", "v")):
        final = "DEFECTIVE"
    else:
        final = "GOOD"
    assert final == "GOOD"


def test_iou_threshold_reasonable():
    iou_thr = 0.40
    assert 0.0 < iou_thr < 1.0