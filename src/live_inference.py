import argparse
import csv
import json
import os
import random
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import psutil
import pynvml
from harvesters.core import Harvester

import inference
from src.config import load_all


# ============================================================
# Config (all thresholds / paths come from configs/*.yaml)
# ============================================================
CFG = load_all()
DET = CFG["detection"]
SEG = CFG["segmentation"]
OCR_CFG = CFG["ocr"]
GEOM = CFG["geometry"]
TRACK = CFG["tracking"]
PIPE = CFG["pipeline"]
CAM = CFG["camera"]


# ============================================================
# CLI arguments
# ============================================================
def parse_cli_arguments():
    """Parse the command-line flags for the live/folder inference entry point."""
    parser = argparse.ArgumentParser(
        description="Frosch bottle live/folder inference pipeline (GPU-optimized)"
    )
    parser.add_argument(
        "--input",
        "--input-mode",
        dest="input_mode",
        choices=("camera", "folder"),
        default="camera",
        help="Input source: camera (default) or folder",
    )
    parser.add_argument(
        "--frame-dir",
        dest="frame_dir",
        type=str,
        default=None,
        help="Directory containing image frames (required when --input folder)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable lightweight pipeline timing/profiling output.",
    )
    return parser.parse_args()


CLI_ARGS = parse_cli_arguments()

# Paths / names from pipeline config
CSV_LOG_PATH = PIPE.get("csv_name", "bottles_data.csv")
JSON_LOG_PATH = PIPE.get("json_name", "bottles_data.json")

with open(CSV_LOG_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Bottle #",
        "defect",
        "tilt",
        "H offset",
        "V offset",
        "Capacity",
    ])

bottle_result_records = []

INPUT_MODE = CLI_ARGS.input_mode
FRAME_DIR = CLI_ARGS.frame_dir

# Camera
CAMERA_CTI_PATH = CAM.get(
    "cti_path",
    "/home/xisai/Downloads/VimbaX_2026-2/cti/VimbaCameraSimulatorTL.cti",
)

# Detection / tracking (from config)
DEFAULT_DETECTION_THRESHOLD = float(DET.get("score_threshold_default", 0.4))
TRACK_IOU_THRESHOLD = float(TRACK.get("iou_threshold", 0.4))
TRACK_MAX_MISSING_FRAMES = int(TRACK.get("max_missing_frames", 20))

CAPTURE_LINE_X_RATIO = float(TRACK.get("trigger_line_frac", 0.40))
CAPTURE_LINE_TOLERANCE_PX = int(TRACK.get("trigger_line_tolerance_px", 20))

FULL_VIEW_X_MARGIN_PX = int(TRACK.get("full_view_x_margin_px", 20))

# Geometry
HORIZONTAL_CENTER_TOLERANCE = float(GEOM.get("horizontal_center_tolerance", 0.15))
VERTICAL_OFFSET_TOLERANCE = float(GEOM.get("vertical_offset_tolerance", 0.05))

CAPACITY_ML_TO_EXPECTED_V_OFFSET = {
    int(k): float(v) for k, v in GEOM.get("expected_v_offset", {}).items()
}


def resolve_expected_v_offset(track=None, capacity=None):
    """Look up the expected label vertical offset for a bottle's detected capacity."""
    cap = capacity
    if cap is None and track is not None:
        cap = track.get("capacity")
    return CAPACITY_ML_TO_EXPECTED_V_OFFSET.get(cap)


LABEL_MATCH_TOLERANCE_PX = int(GEOM.get("label_match_tolerance_px", 10))
CENTER_OFFSET_JUMP_TOLERANCE = float(GEOM.get("spatial_jump_tolerance", 0.08))
CENTER_HISTORY_MIN_SAMPLES = int(GEOM.get("min_history", 3))
CENTER_HISTORY_WINDOW_SIZE = int(GEOM.get("history_window", 5))
MIN_RELIABLE_CENTER_SAMPLES = int(GEOM.get("min_reliable_center_samples", 3))

DEFECT_CONFIRM_STREAK = int(TRACK.get("defect_confirm_streak", 1))
DEFECT_STREAK_GRACE_FRAMES = int(TRACK.get("defect_missing_tolerance", 1))
MIN_COMPLETE_BOTTLE_AREA_PX = int(TRACK.get("min_complete_bottle_area_px", 20000))

# Save roots / video
ANNOTATED_IMAGE_ROOT = os.path.join(
    os.getcwd(), PIPE.get("annotated_root", "image_with_annotation")
)
RAW_IMAGE_ROOT = os.path.join(
    os.getcwd(), PIPE.get("raw_root", "image_without_annotation")
)
for _base in (ANNOTATED_IMAGE_ROOT, RAW_IMAGE_ROOT):
    os.makedirs(os.path.join(_base, "ok"), exist_ok=True)
    os.makedirs(os.path.join(_base, "defective"), exist_ok=True)

CROP_SAVE_PADDING_PX = int(PIPE.get("crop_save_padding_px", 20))
OUTPUT_VIDEO_PATH = os.path.join(
    os.getcwd(), PIPE.get("video_name", "live_stream.mp4")
)
video_writer = None
OUTPUT_VIDEO_FPS = float(PIPE.get("video_fps", 20.0))

PROFILE_ENABLED = bool(CLI_ARGS.profile)
inference.configure_profiling(PROFILE_ENABLED)

# ---------- Pipeline (detection + segmentation + OCR) ----------
pipeline = inference.BottlePipeline(ocr_gpu=bool(OCR_CFG.get("use_gpu", True)))

# NVML monitoring
pynvml.nvmlInit()
_gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)


def query_gpu_stats():
    """Return (gpu_util_percent, mem_used_mb, mem_total_mb), or zeros on failure."""
    try:
        util = pynvml.nvmlDeviceGetUtilizationRates(_gpu_handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(_gpu_handle)
        return util.gpu, mem.used / 1024**2, mem.total / 1024**2
    except Exception:
        return 0, 0, 0


class FrameTimingProfiler:
    """Accumulates per-frame stage timings and periodically prints an average."""

    def __init__(self, enabled=False, report_every=30):
        self.enabled = bool(enabled)
        self.report_every = max(1, int(report_every))
        self.count = 0
        self.acc = {}
        self.last_report = None

    def add(self, **values):
        """Accumulate one frame's worth of named timing values."""
        if not self.enabled:
            return
        self.count += 1
        for key, value in values.items():
            if value is None:
                continue
            self.acc[key] = self.acc.get(key, 0.0) + float(value)
        if self.count % self.report_every == 0:
            self.report()

    def report(self):
        """Print the running average of every tracked timing key, then reset."""
        if not self.enabled or self.count == 0:
            return
        avgs = {k: v / self.count for k, v in self.acc.items()}
        parts = [f"frames={self.count}"]
        preferred = (
            "capture_ms", "preprocess_ms", "detection_trt_ms",
            "segmentation_trt_ms", "gpu_post_ms", "cpu_post_ms",
            "ocr_ms", "save_ms", "save_submit_ms", "total_ms", "fps"
        )
        for key in preferred:
            if key in avgs:
                parts.append(f"{key}={avgs[key]:.2f}")
        print("[PROFILE] " + " | ".join(parts))
        self.acc.clear()
        self.count = 0


profiler = FrameTimingProfiler(PROFILE_ENABLED)

# -----------------------------------------
total_bottles_seen = 0
total_bottles_completed = 0
total_bottles_ok = 0
total_bottles_defective = 0
total_bottles_incomplete = 0
# FPS statistics: only frames containing at least one bottle are included.
bottle_fps_accumulator = 0.0
bottle_fps_sample_count = 0
bottle_fps_running_avg = 0.0
next_track_identifier = 0
engine_fps_accumulator = 0.0
engine_fps_sample_count = 0
active_tracks = []

_save_pool = ThreadPoolExecutor(max_workers=2)


def run_ocr(image, box):
    """OCR one capacity-marking crop, with profiling and the confidence gate applied."""
    ocr_t0 = time.perf_counter() if PROFILE_ENABLED else 0.0
    text, conf = pipeline.read_capacity_from_box(image, box)
    result = text if (text is not None and conf >= inference.OCR_MIN_CONF) else None
    if PROFILE_ENABLED:
        profiler.acc["ocr_ms"] = profiler.acc.get("ocr_ms", 0.0) + (time.perf_counter() - ocr_t0) * 1000.0
    return result


def most_common_capacity(values):
    """Majority-vote a list of observed capacities down to a single stable value."""
    clean = [int(v) for v in values if v in {100, 300, 500}]
    if not clean:
        return None
    counts = Counter(clean)
    return max(counts, key=counts.get)


def box_centroid_xy(box):
    """Center point (x, y) of an (x1, y1, x2, y2) box."""
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def tracks_match(current_box, previous_box):
    """Whether `current_box` is likely the same bottle as the track's `previous_box`."""
    if inference.box_iou(current_box, previous_box) > TRACK_IOU_THRESHOLD:
        return True
    cx, cy = box_centroid_xy(current_box)
    px, py = box_centroid_xy(previous_box)
    current_w = max(1.0, current_box[2] - current_box[0])
    current_h = max(1.0, current_box[3] - current_box[1])
    previous_w = max(1.0, previous_box[2] - previous_box[0])
    previous_h = max(1.0, previous_box[3] - previous_box[1])
    max_w = max(current_w, previous_w)
    max_h = max(current_h, previous_h)
    horizontal_distance = abs(cx - px)
    vertical_distance = abs(cy - py)
    return (
        horizontal_distance <= max_w * 0.75
        and vertical_distance <= max_h * 0.45
    )


def draw_dashed_line(img, pt1, pt2, color, thickness=2, dash_length=12, gap_length=8):
    """Draw a dashed line segment between two points."""
    x1, y1 = pt1
    x2, y2 = pt2
    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if dist < 1e-6:
        return
    dx = (x2 - x1) / dist
    dy = (y2 - y1) / dist
    drawn = 0.0
    while drawn < dist:
        start = drawn
        end = min(drawn + dash_length, dist)
        sx = int(round(x1 + dx * start))
        sy = int(round(y1 + dy * start))
        ex = int(round(x1 + dx * end))
        ey = int(round(y1 + dy * end))
        cv2.line(img, (sx, sy), (ex, ey), color, thickness, cv2.LINE_AA)
        drawn += dash_length + gap_length


def render_status_panel(
    image,
    total_bottles,
    bottle_ok,
    ok_bottles,
    defective_bottles,
    capacity,
    label_pass,
    panel_pass,
    start_x=10,
    start_y=10,
    bottle_detected=True,
):
    """Draw the top-left summary panel (totals, current bottle status, capacity)."""
    capacity_text = capacity if capacity is not None else "00"
    if not bottle_detected:
        bottle_text = "--"
    elif bottle_ok:
        bottle_text = "OK"
    else:
        bottle_text = "Defective"
    lines = [
        f"Total bottles: {total_bottles}",
        f"Bottle: {bottle_text}",
        f"OK bottles: {ok_bottles}",
        f"Defective bottles: {defective_bottles}",
        f"Capacity: {capacity_text} ml",
    ]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 2
    line_height = 26
    padding_x = 12
    padding_y = 10
    box_w = 290
    box_h = padding_y * 2 + line_height * len(lines)
    h_img, w_img = image.shape[:2]
    if start_x + box_w > w_img - 5:
        start_x = max(5, w_img - box_w - 5)
    if start_y + box_h > h_img - 5:
        start_y = max(5, h_img - box_h - 5)
    border_color = (0, 200, 0) if panel_pass else (0, 0, 220)
    overlay = image.copy()
    cv2.rectangle(overlay, (start_x, start_y), (start_x + box_w, start_y + box_h), (0, 0, 0), -1)
    image[:] = cv2.addWeighted(overlay, 0.65, image, 0.35, 0)
    cv2.rectangle(image, (start_x, start_y), (start_x + box_w, start_y + box_h), border_color, 2)
    for i, text in enumerate(lines):
        y = start_y + padding_y + (i + 1) * line_height - 6
        cv2.putText(image, text, (start_x + padding_x, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


def render_mask_contour(image, orientation_data, color=(0, 255, 0), thickness=3, fill=False):
    """Draw a mask's contour outline (and optionally a light fill) onto `image`."""
    if orientation_data is None:
        return
    contour = orientation_data.get("mask_contour")
    if contour is None or len(contour) < 3:
        return
    pts = np.asarray(contour, dtype=np.float32).reshape(-1, 1, 2)
    pts = np.round(pts).astype(np.int32)
    if fill:
        overlay = image.copy()
        cv2.fillPoly(overlay, [pts], color)
        image[:] = cv2.addWeighted(overlay, 0.14, image, 0.86, 0)
    cv2.polylines(image, [pts], True, color, thickness, cv2.LINE_AA)


def render_orientation_axis(image, orientation_data, color=(255, 0, 0), thickness=3):
    """Draw the major/minor orientation axes and center marker for a mask."""
    if orientation_data is None:
        return
    cx, cy = orientation_data["center"]
    dx, dy = orientation_data["major"]
    mx, my = orientation_data["minor"]
    half_length = orientation_data["half_length"]
    cx, cy = int(round(cx)), int(round(cy))
    p1 = (int(round(cx - dx * half_length)), int(round(cy - dy * half_length)))
    p2 = (int(round(cx + dx * half_length)), int(round(cy + dy * half_length)))
    cv2.line(image, p1, p2, color, thickness, cv2.LINE_AA)
    minor_half = max(15.0, half_length * 0.25)
    q1 = (int(round(cx - mx * minor_half)), int(round(cy - my * minor_half)))
    q2 = (int(round(cx + mx * minor_half)), int(round(cy + my * minor_half)))
    cv2.line(image, q1, q2, color, max(1, thickness - 1), cv2.LINE_AA)
    cv2.drawMarker(image, (cx, cy), color, cv2.MARKER_CROSS, 18, 2)


def bottle_fully_in_frame(box, frame_shape):
    """Whether a bottle box sits fully inside the frame, away from the horizontal margins."""
    frame_h, frame_w = frame_shape[:2]
    x1, y1, x2, y2 = map(int, box)
    return (
        x1 >= FULL_VIEW_X_MARGIN_PX
        and x2 <= frame_w - FULL_VIEW_X_MARGIN_PX
        and y1 >= 0
        and y2 <= frame_h
    )


def compute_centricity_offsets(bottle_box, label_box, bottle_mask=None, label_mask=None, expected_v=None):
    """Compute H/V label-vs-bottle offsets and their PASS/FAIL/Pending status."""
    bottle_c = inference.compute_mask_centroid(bottle_mask)
    label_c = inference.compute_mask_centroid(label_mask)
    bx, by = bottle_c if bottle_c is not None else box_centroid_xy(bottle_box)
    lx, ly = label_c if label_c is not None else box_centroid_xy(label_box)
    bw = max(1.0, float(bottle_box[2] - bottle_box[0]))
    bh = max(1.0, float(bottle_box[3] - bottle_box[1]))
    h_offset = (lx - bx) / bw
    v_offset = (ly - by) / bh
    h_ok = abs(h_offset) <= HORIZONTAL_CENTER_TOLERANCE
    v_ok = None if expected_v is None else abs(v_offset - expected_v) <= VERTICAL_OFFSET_TOLERANCE
    return (
        "PASS" if h_ok else "FAIL",
        "Pending" if v_ok is None else ("PASS" if v_ok else "FAIL"),
        h_offset,
        v_offset,
        (bx, by),
        (lx, ly),
    )


def crossed_capture_line(track, box, frame_width):
    """Update/track the trigger-line crossing state for a bottle and return whether it just crossed."""
    line_x = int(frame_width * CAPTURE_LINE_X_RATIO)
    current_center_x = (box[0] + box[2]) / 2.0
    previous_center_x = track.get("previous_center_x")
    crossed = False
    if previous_center_x is not None:
        previous_side = previous_center_x - line_x
        current_side = current_center_x - line_x
        if previous_side * current_side <= 0 and abs(current_center_x - previous_center_x) >= CAPTURE_LINE_TOLERANCE_PX:
            crossed = True
    track["previous_center_x"] = current_center_x
    if crossed:
        track["trigger_crossed"] = True
    return crossed


def new_track_state(box):
    """Create a fresh tracking record for a newly-seen bottle."""
    global next_track_identifier
    track = {
        "id": next_track_identifier,
        "box": box,
        "capacity": None,
        "defects": [],
        "defect_streaks": {"damage": 0, "bump": 0},
        "defect_missing_frames": {"damage": 0, "bump": 0},
        "orientation": None,
        "orientation_data": None,
        "_current_bottle_mask": None,
        "best_complete_orientation_data": None,
        "best_defect_orientation_data": None,
        "h_center": None,
        "v_center": None,
        "missing": 0,
        "saved": False,
        "frames_seen": 0,
        "previous_center_x": None,
        "trigger_crossed": False,
        "best_box": box,
        "best_frame": None,
        "best_complete_box": None,
        "best_complete_frame": None,
        "best_complete_label_box": None,
        "best_complete_capacity_boxes": [],
        "best_complete_damage_boxes": [],
        "best_complete_bump_boxes": [],
        "best_defect_frame": None,
        "best_defect_box": None,
        "best_defect_label_box": None,
        "best_defect_capacity_boxes": [],
        "best_defect_damage_boxes": [],
        "best_defect_bump_boxes": [],
        "best_complete_defect_frame": None,
        "best_complete_defect_box": None,
        "best_complete_defect_label_box": None,
        "best_complete_defect_capacity_boxes": [],
        "best_complete_defect_damage_boxes": [],
        "best_complete_defect_bump_boxes": [],
        "best_complete_defect_orientation_data": None,
        "best_defect_damage_relative": [],
        "best_defect_bump_relative": [],
        "best_valid_box": None,
        "best_valid_frame": None,
        "annotation_label_box": None,
        "annotation_damage_boxes": [],
        "annotation_bump_boxes": [],
        "best_valid_h_center": None,
        "best_valid_v_center": None,
        "best_valid_centricity_error": None,
        "centricity_offset_history": [],
        "h_history": [],
        "v_history": [],
        "orientation_history": [],
        "h_value_history": [],
        "v_value_history": [],
        "orientation_angle_history": [],
        "final_h_value": None,
        "final_v_value": None,
        "final_orientation_angle": None,
        "capacity_history": [],
        "finalized": False,
        "final_status": None,
    }
    next_track_identifier += 1
    return track


def majority_vote(values):
    """Majority PASS/FAIL over a list of values (ties resolve to PASS)."""
    clean = [v for v in values if v in {"PASS", "FAIL"}]
    if not clean:
        return None
    passes = clean.count("PASS")
    fails = clean.count("FAIL")
    return "PASS" if passes >= fails else "FAIL"


def stable_vote(values):
    """Alias kept for parity with the original alias function."""
    return majority_vote(values)


def median_of_valid(values):
    """Median of the finite, non-None values in the list."""
    clean = [float(v) for v in values if v is not None and np.isfinite(float(v))]
    if not clean:
        return None
    return float(np.median(clean))


def format_measurement_text(value, status, suffix=""):
    """Render a numeric measurement + status as display text."""
    if value is None:
        return status or "N/A"
    if status in {"PASS", "FAIL"}:
        return f"{value:.3f}{suffix} ({status})"
    return f"{value:.3f}{suffix} ({status or 'N/A'})"


def finalize_track_measurements(track):
    """Roll up a track's per-frame history into final H/V/tilt/capacity/status values."""
    if track.get("capacity") is None:
        stable_cap = most_common_capacity(track.get("capacity_history", []))
        if stable_cap is not None:
            track["capacity"] = stable_cap
    expected_v = resolve_expected_v_offset(track)
    h_values = [abs(float(x)) for x in track.get("h_value_history", []) if x is not None and np.isfinite(float(x))]
    v_values = [abs(float(x)) for x in track.get("v_value_history", []) if x is not None and np.isfinite(float(x))]
    if h_values:
        h = "PASS" if float(np.median(h_values)) <= HORIZONTAL_CENTER_TOLERANCE else "FAIL"
    else:
        h = "Pending"
    if v_values and expected_v is not None:
        v = "PASS" if abs(float(np.median(v_values)) - expected_v) <= VERTICAL_OFFSET_TOLERANCE else "FAIL"
    else:
        v = "Pending"
    if h == "Pending" or v == "Pending":
        fallback_box = track.get("best_complete_box")
        fallback_label = track.get("best_complete_label_box")
        if fallback_box is not None and fallback_label is not None:
            bx_c = (fallback_box[0] + fallback_box[2]) / 2.0
            by_c = (fallback_box[1] + fallback_box[3]) / 2.0
            lx_c = (fallback_label[0] + fallback_label[2]) / 2.0
            ly_c = (fallback_label[1] + fallback_label[3]) / 2.0
            bw_c = max(1.0, float(fallback_box[2] - fallback_box[0]))
            bh_c = max(1.0, float(fallback_box[3] - fallback_box[1]))
            h_off_c = (lx_c - bx_c) / bw_c
            v_off_c = (ly_c - by_c) / bh_c
            if h == "Pending":
                h = "PASS" if abs(h_off_c) <= HORIZONTAL_CENTER_TOLERANCE else "FAIL"
                track["final_h_value"] = abs(h_off_c)
            if v == "Pending" and expected_v is not None:
                v = "PASS" if abs(v_off_c - expected_v) <= VERTICAL_OFFSET_TOLERANCE else "FAIL"
                track["final_v_value"] = abs(v_off_c)
    track["h_center"] = h
    track["v_center"] = v
    orientation = majority_vote(track.get("orientation_history", []))
    h_numeric = median_of_valid([abs(v) for v in track.get("h_value_history", [])])
    v_numeric = median_of_valid([abs(v) for v in track.get("v_value_history", [])])
    if h_numeric is not None:
        track["final_h_value"] = h_numeric
    if v_numeric is not None:
        track["final_v_value"] = v_numeric
    track["final_orientation_angle"] = median_of_valid(track.get("orientation_angle_history", []))
    if track["h_center"] is None:
        track["h_center"] = "Pending"
    if track["v_center"] is None:
        track["v_center"] = "Pending"
    if track["orientation"] is None:
        track["orientation"] = "Pending"
    track["finalized"] = True
    missing_measurement = any(track[key] == "Pending" for key in ("orientation", "h_center", "v_center"))
    if missing_measurement:
        track["final_status"] = "INCOMPLETE"
    elif bool(track["defects"]) or any(track[key] == "FAIL" for key in ("orientation", "h_center", "v_center")):
        track["final_status"] = "DEFECTIVE"
    else:
        track["final_status"] = "GOOD"
    return track["final_status"]


def analyze_new_bottle(frame, bottle_box, capacity_boxes, label_boxes, damage_boxes, bump_boxes):
    """Placeholder initial analysis for a brand-new track; real values are filled in as frames arrive."""
    result = {"capacity": None, "defects": [], "orientation": None, "h_center": None, "v_center": None}
    result["defects"] = []
    return result


def status_to_color(status):
    """Map a PASS/FAIL/other status onto a BGR display color."""
    if status == "PASS":
        return (0, 220, 0)
    if status == "FAIL":
        return (0, 0, 220)
    return (255, 255, 255)


def render_saved_bottle_annotation(image, bottle_box, track, label_box=None, damage_boxes=None, bump_boxes=None, capacity_boxes=None, orientation_data=None):
    """Draw the full annotation overlay (boxes, orientation, metric panel) onto a saved crop."""
    h_img, w_img = image.shape[:2]
    x1, y1, x2, y2 = map(int, bottle_box)
    x1 = max(0, min(x1, w_img - 1))
    y1 = max(0, min(y1, h_img - 1))
    x2 = max(0, min(x2, w_img - 1))
    y2 = max(0, min(y2, h_img - 1))
    bottle_color = (0, 255, 0)
    label_color = (0, 255, 0)
    capacity_color = (0, 255, 255)
    defect_color = (0, 0, 255)
    cv2.rectangle(image, (x1, y1), (x2, y2), bottle_color, 3)
    bottle_cx = int(round((x1 + x2) / 2))
    bottle_cy = int(round((y1 + y2) / 2))
    if orientation_data is not None:
        render_orientation_axis(image, orientation_data, color=(0, 0, 255), thickness=3)
    if label_box is not None:
        lx1, ly1, lx2, ly2 = map(int, label_box)
        lx1 = max(0, min(lx1, w_img - 1))
        ly1 = max(0, min(ly1, h_img - 1))
        lx2 = max(0, min(lx2, w_img - 1))
        ly2 = max(0, min(ly2, h_img - 1))
        if lx2 > lx1 and ly2 > ly1:
            cv2.rectangle(image, (lx1, ly1), (lx2, ly2), label_color, 3)
            cv2.putText(image, "LABEL", (lx1, max(20, ly1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, label_color, 2, cv2.LINE_AA)
            label_cx = int(round((lx1 + lx2) / 2))
            label_cy = int(round((ly1 + ly2) / 2))
            cv2.drawMarker(image, (label_cx, label_cy), label_color, cv2.MARKER_CROSS, 20, 2)
            cv2.line(image, (label_cx, bottle_cy), (label_cx, label_cy), (0, 0, 255), 3, cv2.LINE_AA)
            cv2.line(image, (bottle_cx, bottle_cy), (label_cx, label_cy), (255, 255, 255), 1, cv2.LINE_AA)
    for cap_box in capacity_boxes or []:
        cx1, cy1, cx2, cy2 = map(int, cap_box)
        cx1 = max(0, min(cx1, w_img - 1))
        cy1 = max(0, min(cy1, h_img - 1))
        cx2 = max(0, min(cx2, w_img - 1))
        cy2 = max(0, min(cy2, h_img - 1))
        if cx2 > cx1 and cy2 > cy1:
            cv2.rectangle(image, (cx1, cy1), (cx2, cy2), capacity_color, 2)
            cv2.putText(image, "CAPACITY", (cx1, max(20, cy1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, capacity_color, 2, cv2.LINE_AA)
    for defect_box in damage_boxes or []:
        dx1, dy1, dx2, dy2 = map(int, defect_box)
        dx1 = max(0, min(dx1, w_img - 1))
        dy1 = max(0, min(dy1, h_img - 1))
        dx2 = max(0, min(dx2, w_img - 1))
        dy2 = max(0, min(dy2, h_img - 1))
        if dx2 > dx1 and dy2 > dy1:
            cv2.rectangle(image, (dx1, dy1), (dx2, dy2), defect_color, 3)
            cv2.putText(image, "DAMAGE", (dx1, max(20, dy1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, defect_color, 2, cv2.LINE_AA)
    for defect_box in bump_boxes or []:
        bx1, by1, bx2, by2 = map(int, defect_box)
        bx1 = max(0, min(bx1, w_img - 1))
        by1 = max(0, min(by1, h_img - 1))
        bx2 = max(0, min(bx2, w_img - 1))
        by2 = max(0, min(by2, h_img - 1))
        if bx2 > bx1 and by2 > by1:
            cv2.rectangle(image, (bx1, by1), (bx2, by2), defect_color, 3)
            cv2.putText(image, "BUMP", (bx1, max(20, by1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, defect_color, 2, cv2.LINE_AA)
    orient_status = track.get("orientation")
    h_status = track.get("h_center")
    v_status = track.get("v_center")
    metric_lines = [
        ("H offset: " + (format_measurement_text(track.get("final_h_value"), h_status) if track.get("final_h_value") is not None else (h_status or "Pending")), status_to_color(h_status)),
        ("V offset: " + (format_measurement_text(track.get("final_v_value"), v_status) if track.get("final_v_value") is not None else (v_status or "Pending")), status_to_color(v_status)),
        ("Tilt: " + (format_measurement_text(track.get("final_orientation_angle"), orient_status, " deg") if track.get("final_orientation_angle") is not None else (orient_status or "N/A")), status_to_color(orient_status)),
    ]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 2
    line_height = 24
    text_block_h = line_height * len(metric_lines) + 12
    text_block_w = 240
    text_x = max(x2 + 12, w_img - text_block_w - 12)
    if text_x + text_block_w > w_img - 5:
        text_x = max(5, w_img - text_block_w - 8)
    panel_bottom = 190
    text_y = max(panel_bottom if text_x < 320 else 20, min(y1 + 10, h_img - text_block_h - 5))
    overlay = image.copy()
    cv2.rectangle(overlay, (text_x - 6, text_y - 8), (text_x + text_block_w, text_y + text_block_h), (0, 0, 0), -1)
    image[:] = cv2.addWeighted(overlay, 0.55, image, 0.45, 0)
    for i, (line, color) in enumerate(metric_lines):
        cv2.putText(image, line, (text_x, text_y + (i + 1) * line_height - 4), font, font_scale, color, thickness, cv2.LINE_AA)


def persist_bottle_images(frame, track):
    """Crop, annotate, and save both the raw and annotated images for a finalized bottle."""
    save_t0 = time.perf_counter() if PROFILE_ENABLED else 0.0
    global total_bottles_completed, total_bottles_ok, total_bottles_defective, total_bottles_incomplete, bottle_result_records
    if track["saved"] or not track.get("finalized", False):
        return False
    saved_orientation_data = None
    if track.get("best_complete_defect_frame") is not None and track.get("defects"):
        frame = track["best_complete_defect_frame"]
        box = track["best_complete_defect_box"]
        saved_label_box = track.get("best_complete_defect_label_box")
        saved_capacity_boxes = track.get("best_complete_defect_capacity_boxes") or track.get("best_complete_capacity_boxes", [])
        saved_damage_boxes = track.get("best_complete_defect_damage_boxes", [])
        saved_bump_boxes = track.get("best_complete_defect_bump_boxes", [])
        saved_orientation_data = track.get("best_complete_defect_orientation_data")
    elif track["best_complete_frame"] is not None:
        frame = track["best_complete_frame"]
        box = track["best_complete_box"]
        saved_label_box = track.get("best_complete_label_box")
        saved_capacity_boxes = track.get("best_complete_capacity_boxes", [])
        saved_damage_boxes = track.get("best_complete_damage_boxes", [])
        saved_bump_boxes = track.get("best_complete_bump_boxes", [])
        saved_orientation_data = track.get("best_complete_orientation_data")
    elif track.get("best_defect_frame") is not None and track.get("defects"):
        frame = track["best_defect_frame"]
        box = track["best_defect_box"]
        saved_label_box = track.get("best_defect_label_box")
        saved_capacity_boxes = track.get("best_defect_capacity_boxes") or track.get("best_complete_capacity_boxes", [])
        saved_damage_boxes = track.get("best_defect_damage_boxes", [])
        saved_bump_boxes = track.get("best_defect_bump_boxes", [])
        saved_orientation_data = track.get("best_defect_orientation_data")
    else:
        return False
    bx1, by1, bx2, by2 = map(int, box)
    bw = max(1.0, float(bx2 - bx1))
    bh = max(1.0, float(by2 - by1))
    if "bump" in track["defects"] and not saved_bump_boxes:
        saved_bump_boxes = track.get("best_complete_bump_boxes", [])
        if not saved_bump_boxes:
            saved_bump_boxes = [(int(round(bx1 + rx1 * bw)), int(round(by1 + ry1 * bh)), int(round(bx1 + rx2 * bw)), int(round(by1 + ry2 * bh))) for rx1, ry1, rx2, ry2 in track.get("best_defect_bump_relative", [])]
    if "damage" in track["defects"] and not saved_damage_boxes:
        saved_damage_boxes = track.get("best_complete_damage_boxes", [])
        if not saved_damage_boxes:
            saved_damage_boxes = [(int(round(bx1 + rx1 * bw)), int(round(by1 + ry1 * bh)), int(round(bx1 + rx2 * bw)), int(round(by1 + ry2 * bh))) for rx1, ry1, rx2, ry2 in track.get("best_defect_damage_relative", [])]
    x1, y1, x2, y2 = map(int, box)
    frame_h, frame_w = frame.shape[:2]
    x1 = max(0, x1 - CROP_SAVE_PADDING_PX)
    y1 = max(0, y1 - CROP_SAVE_PADDING_PX)
    x2 = min(frame_w, x2 + CROP_SAVE_PADDING_PX)
    y2 = min(frame_h, y2 + CROP_SAVE_PADDING_PX)
    if x2 <= x1 or y2 <= y1:
        return False
    original_crop = frame[y1:y2, x1:x2].copy()
    if original_crop.size == 0:
        return False
    annotated_crop = original_crop.copy()
    local_box = (int(box[0] - x1), int(box[1] - y1), int(box[2] - x1), int(box[3] - y1))

    def to_local_box(saved_box):
        if saved_box is None:
            return None
        return (int(saved_box[0] - x1), int(saved_box[1] - y1), int(saved_box[2] - x1), int(saved_box[3] - y1))

    local_label_box = to_local_box(saved_label_box)
    local_capacity_boxes = [to_local_box(b) for b in (saved_capacity_boxes or []) if b is not None]
    local_damage_boxes = [to_local_box(b) for b in saved_damage_boxes]
    local_bump_boxes = [to_local_box(b) for b in saved_bump_boxes]
    local_orientation_data = saved_orientation_data
    if local_orientation_data is not None:
        contour = local_orientation_data.get("mask_contour")
        local_orientation_data = dict(local_orientation_data)
        ocx, ocy = local_orientation_data["center"]
        local_orientation_data["center"] = (ocx - x1, ocy - y1)
        if contour is not None and len(contour) > 0:
            pts = np.asarray(contour, dtype=np.float32)
            local_pts = pts.copy()
            local_pts[:, 0] -= x1
            local_pts[:, 1] -= y1
            local_orientation_data["mask_contour"] = local_pts.tolist()
    render_saved_bottle_annotation(annotated_crop, local_box, track, label_box=local_label_box, damage_boxes=local_damage_boxes, bump_boxes=local_bump_boxes, capacity_boxes=local_capacity_boxes, orientation_data=local_orientation_data)
    final_status = track.get("final_status")
    if final_status is None:
        missing_measurement = any(track[key] in {None, "Pending"} for key in ("orientation", "h_center", "v_center"))
        if missing_measurement:
            final_status = "INCOMPLETE"
        elif bool(track["defects"]) or any(track[key] == "FAIL" for key in ("orientation", "h_center", "v_center")):
            final_status = "DEFECTIVE"
        else:
            final_status = "GOOD"
        track["final_status"] = final_status
    folder_status = "ok" if final_status == "GOOD" else "defective"
    bottle_num = track["id"] + 1
    filename = f"bottle_{bottle_num:03d}.jpg"
    original_path = os.path.join(RAW_IMAGE_ROOT, folder_status, filename)
    annotated_path = os.path.join(ANNOTATED_IMAGE_ROOT, folder_status, filename)
    original_saved = cv2.imwrite(original_path, original_crop)
    annotated_saved = cv2.imwrite(annotated_path, annotated_crop)
    if original_saved and annotated_saved:
        track["saved"] = True
        track["finalized"] = True
        track["final_status"] = final_status
        total_bottles_completed += 1
        if final_status == "GOOD":
            total_bottles_ok += 1
        else:
            total_bottles_defective += 1
        defect_str = ", ".join(track["defects"]) if track["defects"] else "None"
        capacity_str = track.get("capacity") if track.get("capacity") is not None else "Not detected"
        print(f"Bottle #{bottle_num} | Defect: {defect_str} | Capacity: {capacity_str}")
        tilt_val = track.get("final_orientation_angle")
        h_val = track.get("final_h_value")
        v_val = track.get("final_v_value")
        row = [bottle_num, defect_str, f"{tilt_val:.3f}" if tilt_val is not None else "", f"{h_val:.3f}" if h_val is not None else "", f"{v_val:.3f}" if v_val is not None else "", capacity_str if capacity_str != "Not detected" else ""]
        with open(CSV_LOG_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        bottle_result_records.append({
            "Bottle #": bottle_num,
            "defect": defect_str,
            "tilt": float(tilt_val) if tilt_val is not None else None,
            "H offset": float(h_val) if h_val is not None else None,
            "V offset": float(v_val) if v_val is not None else None,
            "Capacity": track.get("capacity"),
        })
        if PROFILE_ENABLED:
            profiler.acc["save_ms"] = profiler.acc.get("save_ms", 0.0) + (time.perf_counter() - save_t0) * 1000.0
        return True
    return False


def match_label_to_bottle(bottle_box, label_boxes):
    """Pick the best label box belonging to `bottle_box` (closest center, largest area)."""
    bx, by = box_centroid_xy(bottle_box)
    candidates = []
    for lbl_box in label_boxes:
        label_overlaps_bottle = (
            lbl_box[2] > bottle_box[0] - LABEL_MATCH_TOLERANCE_PX
            and lbl_box[0] < bottle_box[2] + LABEL_MATCH_TOLERANCE_PX
            and lbl_box[3] > bottle_box[1] - LABEL_MATCH_TOLERANCE_PX
            and lbl_box[1] < bottle_box[3] + LABEL_MATCH_TOLERANCE_PX
        )
        if not label_overlaps_bottle:
            continue
        clipped_label_box = (
            max(lbl_box[0], bottle_box[0]),
            max(lbl_box[1], bottle_box[1]),
            min(lbl_box[2], bottle_box[2]),
            min(lbl_box[3], bottle_box[3]),
        )
        if clipped_label_box[2] <= clipped_label_box[0] or clipped_label_box[3] <= clipped_label_box[1]:
            continue
        lx, ly = box_centroid_xy(clipped_label_box)
        bw = max(1.0, float(bottle_box[2] - bottle_box[0]))
        bh = max(1.0, float(bottle_box[3] - bottle_box[1]))
        distance = (((lx - bx) / bw) ** 2 + ((ly - by) / bh) ** 2) ** 0.5
        area = (clipped_label_box[2] - clipped_label_box[0]) * (clipped_label_box[3] - clipped_label_box[1])
        candidates.append((distance, -area, clipped_label_box))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def refresh_centricity_state(track, bottle_box, label_boxes, seg_detections=None, bottle_mask=None, frame=None):
    """Update a track's H/V centricity status from the current frame's label match."""
    clipped_label_box = match_label_to_bottle(bottle_box, label_boxes)
    if clipped_label_box is None:
        return False
    label_mask = inference.select_label_mask(bottle_box, seg_detections, frame) if seg_detections is not None and frame is not None else None
    expected_v = resolve_expected_v_offset(track)
    (_h_status, _v_status, h_offset, v_offset, (bx, by), (lx, ly)) = compute_centricity_offsets(
        bottle_box, clipped_label_box, bottle_mask=bottle_mask, label_mask=label_mask, expected_v=expected_v
    )
    history = track.get("centricity_offset_history", [])
    if len(history) >= CENTER_HISTORY_MIN_SAMPLES:
        previous_h, previous_v = history[-1]
        if abs(h_offset - previous_h) > CENTER_OFFSET_JUMP_TOLERANCE or abs(v_offset - previous_v) > CENTER_OFFSET_JUMP_TOLERANCE:
            return False
    history.append((h_offset, v_offset))
    if len(history) > CENTER_HISTORY_WINDOW_SIZE:
        del history[:-CENTER_HISTORY_WINDOW_SIZE]
    track["centricity_offset_history"] = history
    h = "PASS" if abs(h_offset) <= HORIZONTAL_CENTER_TOLERANCE else "FAIL"
    v = "Pending" if expected_v is None else ("PASS" if abs(v_offset - expected_v) <= VERTICAL_OFFSET_TOLERANCE else "FAIL")
    track["h_center"] = h
    track["v_center"] = v
    return True


def refresh_defect_state(track, bottle_box, damage_boxes, bump_boxes, frame=None, label_box=None, orientation_data=None, bottle_mask=None):
    """Update a track's confirmed-defect streaks and, when confirmed, its best-shot captures."""
    defects = set(track["defects"])
    current_mask = bottle_mask if bottle_mask is not None else track.get("_current_bottle_mask")
    damage_flags = inference.boxes_overlap_mask(damage_boxes, current_mask)
    bump_flags = inference.boxes_overlap_mask(bump_boxes, current_mask)
    damage_valid = any(damage_flags)
    bump_valid = any(bump_flags)
    if damage_valid:
        track["defect_streaks"]["damage"] += 1
        track["defect_missing_frames"]["damage"] = 0
    else:
        if track["defect_streaks"]["damage"] > 0:
            track["defect_missing_frames"]["damage"] += 1
            if track["defect_missing_frames"]["damage"] > DEFECT_STREAK_GRACE_FRAMES:
                track["defect_streaks"]["damage"] = 0
                track["defect_missing_frames"]["damage"] = 0
    if bump_valid:
        track["defect_streaks"]["bump"] += 1
        track["defect_missing_frames"]["bump"] = 0
    else:
        if track["defect_streaks"]["bump"] > 0:
            track["defect_missing_frames"]["bump"] += 1
            if track["defect_missing_frames"]["bump"] > DEFECT_STREAK_GRACE_FRAMES:
                track["defect_streaks"]["bump"] = 0
                track["defect_missing_frames"]["bump"] = 0
    if track["defect_streaks"]["damage"] >= DEFECT_CONFIRM_STREAK:
        defects.add("damage")
    if track["defect_streaks"]["bump"] >= DEFECT_CONFIRM_STREAK:
        defects.add("bump")
    track["defects"] = sorted(defects)
    confirmed_defect = (
        (damage_valid and track["defect_streaks"]["damage"] >= DEFECT_CONFIRM_STREAK) or
        (bump_valid and track["defect_streaks"]["bump"] >= DEFECT_CONFIRM_STREAK)
    )
    if confirmed_defect and frame is not None:
        track["best_defect_frame"] = frame.copy()
        track["best_defect_box"] = bottle_box
        track["best_defect_label_box"] = label_box
        track["best_defect_damage_boxes"] = [
            dmg for dmg, valid in zip(damage_boxes, damage_flags) if valid
        ]
        track["best_defect_bump_boxes"] = [
            bump for bump, valid in zip(bump_boxes, bump_flags) if valid
        ]
        bx1, by1, bx2, by2 = map(int, bottle_box)
        bw = max(1.0, float(bx2 - bx1))
        bh = max(1.0, float(by2 - by1))
        track["best_defect_damage_relative"] = [((dmg[0] - bx1) / bw, (dmg[1] - by1) / bh, (dmg[2] - bx1) / bw, (dmg[3] - by1) / bh) for dmg in track["best_defect_damage_boxes"]]
        track["best_defect_bump_relative"] = [((bump[0] - bx1) / bw, (bump[1] - by1) / bh, (bump[2] - bx1) / bw, (bump[3] - by1) / bh) for bump in track["best_defect_bump_boxes"]]
        track["best_defect_orientation_data"] = orientation_data
        frame_h, frame_w = frame.shape[:2]
        dx1, dy1, dx2, dy2 = map(int, bottle_box)
        bottle_is_complete = dx1 > 0 and dy1 > 0 and dx2 < frame_w and dy2 < frame_h
        if bottle_is_complete:
            current_area = max(0, dx2 - dx1) * max(0, dy2 - dy1)
            if track["best_complete_defect_box"] is None:
                should_store = True
            else:
                cx1, cy1, cx2, cy2 = map(int, track["best_complete_defect_box"])
                previous_area = max(0, cx2 - cx1) * max(0, cy2 - cy1)
                should_store = current_area > previous_area
            if should_store:
                track["best_complete_defect_frame"] = frame.copy()
                track["best_complete_defect_box"] = bottle_box
                track["best_complete_defect_label_box"] = label_box
                track["best_complete_defect_damage_boxes"] = [
                    dmg for dmg, valid in zip(damage_boxes, damage_flags) if valid
                ]
                track["best_complete_defect_bump_boxes"] = [
                    bump for bump, valid in zip(bump_boxes, bump_flags) if valid
                ]
                if orientation_data is not None:
                    saved_orientation = dict(orientation_data)
                    if orientation_data.get("mask_contour") is not None:
                        saved_orientation["mask_contour"] = [list(point) for point in orientation_data["mask_contour"]]
                    track["best_complete_defect_orientation_data"] = saved_orientation
                else:
                    track["best_complete_defect_orientation_data"] = None


def refresh_best_complete_capture(track, box, frame, label_box=None, damage_boxes=None, bump_boxes=None, capacity_boxes=None, force=False, orientation_data=None):
    """Keep the largest fully-in-frame capture of this bottle around for saving/annotation."""
    if not bottle_fully_in_frame(box, frame.shape):
        return
    x1, y1, x2, y2 = map(int, box)
    current_area = max(0, x2 - x1) * max(0, y2 - y1)
    if current_area < MIN_COMPLETE_BOTTLE_AREA_PX:
        return
    if orientation_data is None and track.get("best_complete_frame") is not None:
        return
    if track["best_complete_box"] is None:
        should_update = True
    else:
        bx1, by1, bx2, by2 = map(int, track["best_complete_box"])
        best_area = max(0, bx2 - bx1) * max(0, by2 - by1)
        should_update = force or (current_area > best_area or (current_area == best_area and track.get("best_complete_label_box") is None and label_box is not None))
    if not should_update:
        return
    track["best_complete_box"] = box
    track["best_complete_frame"] = frame.copy()
    track["best_complete_label_box"] = label_box
    track["best_complete_capacity_boxes"] = list(capacity_boxes or [])
    track["best_complete_damage_boxes"] = list(damage_boxes or [])
    track["best_complete_bump_boxes"] = list(bump_boxes or [])
    if orientation_data is not None:
        saved_orientation = dict(orientation_data)
        if orientation_data.get("mask_contour") is not None:
            saved_orientation["mask_contour"] = [list(point) for point in orientation_data["mask_contour"]]
        track["best_complete_orientation_data"] = saved_orientation
    else:
        track["best_complete_orientation_data"] = None


def refresh_best_valid_capture(track, box, frame, label_box=None, damage_boxes=None, bump_boxes=None, force=False, seg_detections=None, bottle_mask=None):
    """Track the lowest-centricity-error, fully-in-frame capture seen so far."""
    if label_box is None:
        return
    if not bottle_fully_in_frame(box, frame.shape):
        return
    label_mask = inference.select_label_mask(box, seg_detections, frame) if seg_detections is not None else None
    expected_v = resolve_expected_v_offset(track)
    (h, v, h_offset, v_offset, _bc, _lc) = compute_centricity_offsets(box, label_box, bottle_mask=bottle_mask, label_mask=label_mask, expected_v=expected_v)
    h_error = abs(h_offset)
    v_error = 0.0 if expected_v is None else abs(v_offset - expected_v)
    centricity_error = h_error + v_error
    x1, y1, x2, y2 = map(int, box)
    current_area = max(0, x2 - x1) * max(0, y2 - y1)
    previous_error = track.get("best_valid_centricity_error")
    if force or track["best_valid_box"] is None:
        should_update = True
    elif previous_error is None:
        should_update = True
    else:
        bx1, by1, bx2, by2 = map(int, track["best_valid_box"])
        best_area = max(0, bx2 - bx1) * max(0, by2 - by1)
        should_update = centricity_error < previous_error - 1e-6 or (abs(centricity_error - previous_error) <= 1e-6 and current_area > best_area)
    if should_update:
        track["best_valid_box"] = box
        track["best_valid_frame"] = None
        track["annotation_label_box"] = label_box
        track["annotation_damage_boxes"] = list(damage_boxes or [])
        track["annotation_bump_boxes"] = list(bump_boxes or [])
        track["best_valid_h_center"] = h
        track["best_valid_v_center"] = v
        track["best_valid_centricity_error"] = centricity_error


def ready_to_persist_bottle(track, frame_shape, force=False):
    """Whether a track has enough captured state to be finalized and saved now."""
    if track["saved"] or track.get("finalized", False):
        return False
    if not force and track["missing"] < TRACK_MAX_MISSING_FRAMES:
        return False
    if track["best_complete_box"] is None or track["best_complete_frame"] is None:
        return False
    finalize_track_measurements(track)
    return True


class FrameHandle:
    """Context-manager wrapper around a single folder-sourced frame."""

    def __init__(self, frame):
        self.frame = frame

    def __enter__(self):
        return self

    def __exit__(self, exp_type, exp_value, traceback):
        pass


class FolderFrameFeed:
    """Iterates image files in a folder in natural (numeric-aware) filename order."""

    def __init__(self, frame_dir):
        """Discover and sort image frames in `frame_dir`."""
        self.frame_dir = frame_dir
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        self.frames = [os.path.join(frame_dir, name) for name in os.listdir(frame_dir) if os.path.splitext(name)[1].lower() in valid_extensions]
        self.frames.sort(key=lambda path: [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", os.path.basename(path))])
        self.index = 0
        print(f"Frame folder: {frame_dir}")
        print(f"Frames found: {len(self.frames)}")
        if not self.frames:
            raise RuntimeError(f"No image frames found in folder: {frame_dir}")

    def start(self):
        pass

    def stop(self):
        pass

    def fetch(self):
        """Return the next frame wrapped in a FrameHandle, or raise StopIteration."""
        if self.index >= len(self.frames):
            raise StopIteration
        frame_path = self.frames[self.index]
        self.index += 1
        frame = cv2.imread(frame_path)
        if frame is None:
            raise RuntimeError(f"Unable to read frame: {frame_path}")
        return FrameHandle(frame)

    def destroy(self):
        pass


h_cam = None

if INPUT_MODE == "folder":
    if FRAME_DIR is None:
        raise RuntimeError("--frame-dir is required when --input folder")
    ia = FolderFrameFeed(FRAME_DIR)
    ia.start()
    print("Reading frames from folder...")
    print("Press q to exit.")
else:
    h_cam = Harvester()
    h_cam.add_file(CAMERA_CTI_PATH)
    h_cam.update()
    print(f"Devices found: {len(h_cam.device_info_list)}")
    print(f"Annotated images: {ANNOTATED_IMAGE_ROOT}")
    print(f"Original images: {RAW_IMAGE_ROOT}")
    ia = h_cam.create(1)
    ia.start()
    print("Streaming... Press q to exit.")

try:
    while True:
        frame_loop_start = time.perf_counter()
        if INPUT_MODE == "folder":
            try:
                with ia.fetch() as buffer:
                    frame = buffer.frame
            except StopIteration:
                print("All frames have been processed.")
                break
        else:
            with ia.fetch() as buffer:
                component = buffer.payload.components[0]
                width = component.width
                height = component.height
                pixel_format = component.data_format
                data = component.data
                if pixel_format == "Mono8":
                    frame = data.reshape(height, width)
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif pixel_format == "RGB8":
                    frame = data.reshape(height, width, 3)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                elif pixel_format == "BGR8":
                    frame = data.reshape(height, width, 3)
                elif pixel_format in ("BayerRG8", "BayerGB8", "BayerGR8", "BayerBG8"):
                    bayer_map = {
                        "BayerRG8": cv2.COLOR_BayerRG2BGR,
                        "BayerGB8": cv2.COLOR_BayerGB2BGR,
                        "BayerGR8": cv2.COLOR_BayerGR2BGR,
                        "BayerBG8": cv2.COLOR_BayerBG2BGR,
                    }
                    frame = cv2.cvtColor(data.reshape(height, width), bayer_map[pixel_format])
                else:
                    continue

        frame_stage_end = time.perf_counter()
        t0 = frame_stage_end
        inference.reset_frame_mask_cache()

        # ---------- Inference (overlapped dedicated CUDA streams) ----------
        trt_wall_start = time.perf_counter()
        detections, seg_detections = pipeline.detect_and_segment(frame)
        trt_wall_end = time.perf_counter()
        trt_time = trt_wall_end - trt_wall_start
        inference_fps = 1.0 / max(trt_time, 1e-9)
        engine_fps_accumulator += inference_fps
        engine_fps_sample_count += 1
        detection_profile = pipeline.detector.profile_ms() if PROFILE_ENABLED else {}
        segmentation_profile = pipeline.segmenter.profile_ms() if PROFILE_ENABLED else {}

        cpu_decode_start = time.perf_counter()
        bottle_boxes = []
        capacity_boxes = []
        label_boxes = []
        damage_boxes = []
        bump_boxes = []

        display = frame.copy()

        for i, cls in enumerate(detections.data["class_name"]):
            if float(detections.confidence[i]) < inference.CLASS_CONFIDENCE_THRESHOLDS.get(cls, DEFAULT_DETECTION_THRESHOLD):
                continue
            x1, y1, x2, y2 = map(int, detections.xyxy[i])
            if cls == "bottle":
                bottle_boxes.append((x1, y1, x2, y2))
            elif cls == "capacity":
                capacity_boxes.append((x1, y1, x2, y2))
            elif cls == "label":
                label_boxes.append((x1, y1, x2, y2))
            elif cls == "damage":
                damage_boxes.append((x1, y1, x2, y2))
            elif cls == "bump":
                bump_boxes.append((x1, y1, x2, y2))

        _draw_tol = 10
        for bx1, by1, bx2, by2 in bottle_boxes:
            cv2.rectangle(display, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
            cv2.putText(display, "bottle", (bx1, by1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        for cls_name, boxes in (("capacity", capacity_boxes), ("label", label_boxes), ("damage", damage_boxes), ("bump", bump_boxes)):
            for x1, y1, x2, y2 in boxes:
                belongs_to_bottle = any(
                    x2 > bb[0] - _draw_tol and x1 < bb[2] + _draw_tol and
                    y2 > bb[1] - _draw_tol and y1 < bb[3] + _draw_tol
                    for bb in bottle_boxes
                )
                if not belongs_to_bottle:
                    continue
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, cls_name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        for track in active_tracks:
            track["missing"] += 1
            track["frames_seen"] += 1

        for bottle in bottle_boxes:
            matched = False
            for track in active_tracks:
                if tracks_match(bottle, track["box"]):
                    track["box"] = bottle
                    track["missing"] = 0
                    matched = True
                    if track.get("finalized", False) or track.get("saved", False):
                        break

                    current_area = max(0, bottle[2] - bottle[0]) * max(0, bottle[3] - bottle[1])
                    best_area = max(0, track["best_box"][2] - track["best_box"][0]) * max(0, track["best_box"][3] - track["best_box"][1])
                    if current_area > best_area:
                        track["best_box"] = bottle
                        track["best_frame"] = None

                    bottle_mask = inference.select_bottle_mask(bottle, seg_detections)
                    if bottle_mask is not None:
                        bottle_mask = inference.scale_mask_to_frame(bottle_mask, frame)
                        bottle_mask = inference.clip_mask_to_box(bottle_mask, bottle)
                        track["_current_bottle_mask"] = bottle_mask
                        orientation_data = inference.compute_mask_orientation(bottle_mask)
                        if orientation_data is not None:
                            track["orientation_data"] = orientation_data
                            track["orientation"] = orientation_data["status"]
                    else:
                        bottle_mask = track.get("_current_bottle_mask")
                        orientation_data = track.get("orientation_data")

                    centricity_updated = refresh_centricity_state(
                        track, bottle, label_boxes,
                        seg_detections=seg_detections,
                        bottle_mask=bottle_mask,
                        frame=frame,
                    )
                    if centricity_updated:
                        if track["h_center"] in {"PASS", "FAIL"}:
                            track["h_history"].append(track["h_center"])
                        if track["v_center"] in {"PASS", "FAIL"}:
                            track["v_history"].append(track["v_center"])
                    if track["orientation"] in {"PASS", "FAIL"}:
                        track["orientation_history"].append(track["orientation"])
                    if centricity_updated and track.get("centricity_offset_history"):
                        latest_h, latest_v = track["centricity_offset_history"][-1]
                        track["h_value_history"].append(float(latest_h))
                        track["v_value_history"].append(float(latest_v))
                    if orientation_data is not None:
                        angle_deg = orientation_data.get("angle_deg")
                        if angle_deg is not None:
                            track["orientation_angle_history"].append(float(angle_deg))

                    current_label_box = match_label_to_bottle(bottle, label_boxes)
                    current_damage_boxes = [dmg for dmg in damage_boxes if dmg[0] >= bottle[0] and dmg[2] <= bottle[2] and dmg[1] >= bottle[1] and dmg[3] <= bottle[3]]
                    current_bump_boxes = [bump for bump in bump_boxes if bump[0] >= bottle[0] and bump[2] <= bottle[2] and bump[1] >= bottle[1] and bump[3] <= bottle[3]]
                    _cap_tol_disp = 15
                    current_capacity_boxes = [
                        cap for cap in capacity_boxes
                        if cap[0] >= bottle[0] - _cap_tol_disp and cap[2] <= bottle[2] + _cap_tol_disp
                        and cap[1] >= bottle[1] - _cap_tol_disp and cap[3] <= bottle[3] + _cap_tol_disp
                    ]

                    previous_defects = set(track["defects"])
                    refresh_defect_state(track, bottle, current_damage_boxes, current_bump_boxes, frame=frame, label_box=current_label_box, orientation_data=orientation_data, bottle_mask=bottle_mask)
                    defect_changed = set(track["defects"]) != previous_defects

                    refresh_best_complete_capture(track, bottle, frame, label_box=current_label_box, damage_boxes=current_damage_boxes, bump_boxes=current_bump_boxes, capacity_boxes=current_capacity_boxes, force=defect_changed, orientation_data=orientation_data)
                    refresh_best_valid_capture(track, bottle, frame, label_box=current_label_box, damage_boxes=current_damage_boxes, bump_boxes=current_bump_boxes, force=defect_changed, seg_detections=seg_detections, bottle_mask=bottle_mask)

                    # ---------- OCR cadence ----------
                    OCR_INITIAL_FRAME = 1
                    OCR_RETRY_EVERY_N_FRAMES = 5
                    should_run_ocr = (
                        track.get("capacity") is None
                        and (
                            track["frames_seen"] == OCR_INITIAL_FRAME
                            or track["frames_seen"] % OCR_RETRY_EVERY_N_FRAMES == 0
                        )
                    )

                    print(
                        f"[OCR CHECK] Bottle #{track['id'] + 1} | "
                        f"frames={track['frames_seen']} | "
                        f"capacity_boxes={len(capacity_boxes)} | "
                        f"ocr={should_run_ocr}"
                    )

                    if should_run_ocr:
                        observed_capacity = None
                        _cap_tol = 15
                        for cap_box in capacity_boxes:
                            if (cap_box[0] >= bottle[0] - _cap_tol and cap_box[2] <= bottle[2] + _cap_tol and
                                cap_box[1] >= bottle[1] - _cap_tol and cap_box[3] <= bottle[3] + _cap_tol):
                                cap = run_ocr(frame, cap_box)
                                if cap in {100, 300, 500}:
                                    observed_capacity = cap
                                    break
                        if observed_capacity is not None:
                            track["capacity_history"].append(observed_capacity)
                            stable_cap = most_common_capacity(track["capacity_history"])
                            if stable_cap != track.get("capacity"):
                                track["capacity"] = stable_cap
                    # ---------------------------------

                    crossed_capture_line(track, bottle, frame.shape[1])
                    break

            if not matched:
                total_bottles_seen += 1
                track = new_track_state(bottle)
                track["best_frame"] = frame.copy()
                result = analyze_new_bottle(frame, bottle, capacity_boxes, label_boxes, damage_boxes, bump_boxes)
                track["capacity"] = result["capacity"]
                track["defects"] = result["defects"]

                bottle_mask = inference.select_bottle_mask(bottle, seg_detections)
                if bottle_mask is not None:
                    bottle_mask = inference.scale_mask_to_frame(bottle_mask, frame)
                    bottle_mask = inference.clip_mask_to_box(bottle_mask, bottle)
                    track["_current_bottle_mask"] = bottle_mask
                    orientation_data = inference.compute_mask_orientation(bottle_mask)
                    if orientation_data is not None:
                        track["orientation_data"] = orientation_data
                        track["orientation"] = orientation_data["status"]
                else:
                    track["_current_bottle_mask"] = None
                    orientation_data = None

                initial_label_box = match_label_to_bottle(bottle, label_boxes)
                centricity_updated = refresh_centricity_state(track, bottle, label_boxes, seg_detections=seg_detections, bottle_mask=bottle_mask, frame=frame)
                if centricity_updated:
                    if track["h_center"] in {"PASS", "FAIL"}:
                        track["h_history"].append(track["h_center"])
                    if track["v_center"] in {"PASS", "FAIL"}:
                        track["v_history"].append(track["v_center"])
                    if track.get("centricity_offset_history"):
                        latest_h, latest_v = track["centricity_offset_history"][-1]
                        track["h_value_history"].append(float(latest_h))
                        track["v_value_history"].append(float(latest_v))
                if track["orientation"] in {"PASS", "FAIL"}:
                    track["orientation_history"].append(track["orientation"])
                if orientation_data is not None:
                    angle_deg = orientation_data.get("angle_deg")
                    if angle_deg is not None:
                        track["orientation_angle_history"].append(float(angle_deg))
                if track["capacity"] is not None:
                    track["capacity_history"].append(track["capacity"])

                initial_damage_boxes = [dmg for dmg in damage_boxes if dmg[0] >= bottle[0] and dmg[2] <= bottle[2] and dmg[1] >= bottle[1] and dmg[3] <= bottle[3]]
                initial_bump_boxes = [bump for bump in bump_boxes if bump[0] >= bottle[0] and bump[2] <= bottle[2] and bump[1] >= bottle[1] and bump[3] <= bottle[3]]
                _cap_tol_disp = 15
                initial_capacity_boxes = [cap for cap in capacity_boxes if cap[0] >= bottle[0] - _cap_tol_disp and cap[2] <= bottle[2] + _cap_tol_disp and cap[1] >= bottle[1] - _cap_tol_disp and cap[3] <= bottle[3] + _cap_tol_disp]

                refresh_defect_state(track, bottle, initial_damage_boxes, initial_bump_boxes, frame=frame, label_box=initial_label_box, orientation_data=orientation_data)
                refresh_best_complete_capture(track, bottle, frame, label_box=initial_label_box, damage_boxes=initial_damage_boxes, bump_boxes=initial_bump_boxes, capacity_boxes=initial_capacity_boxes, orientation_data=orientation_data)
                refresh_best_valid_capture(track, bottle, frame, label_box=initial_label_box, damage_boxes=initial_damage_boxes, bump_boxes=initial_bump_boxes, seg_detections=seg_detections, bottle_mask=bottle_mask)
                active_tracks.append(track)

        cpu_decode_end = time.perf_counter()

        remaining_tracks = []
        save_submit_start = time.perf_counter()
        for track in active_tracks:
            if track.get("trigger_crossed", False) and not track["saved"]:
                if ready_to_persist_bottle(track, frame.shape, force=True):
                    _save_pool.submit(persist_bottle_images, frame, track)
            elif track["missing"] >= TRACK_MAX_MISSING_FRAMES and not track["saved"]:
                if ready_to_persist_bottle(track, frame.shape, force=True):
                    _save_pool.submit(persist_bottle_images, frame, track)
            if not track["saved"]:
                remaining_tracks.append(track)
            elif track["missing"] < TRACK_MAX_MISSING_FRAMES:
                remaining_tracks.append(track)
        active_tracks = remaining_tracks
        save_submit_ms = (time.perf_counter() - save_submit_start) * 1000.0

        gpu_post_ms = 0.0
        if PROFILE_ENABLED:
            # This wall-time deliberately covers only the Python region that
            # schedules/consumes the mask/PCA/centroid/overlap CUDA work during
            # tracking; the underlying kernel timing lives inside those calls.
            gpu_post_ms = max(0.0, (cpu_decode_end - cpu_decode_start) * 1000.0)

        for track in active_tracks:
            if track["missing"] > 0:
                continue
            x1, y1, x2, y2 = map(int, track["box"])
            bottle_color = (0, 255, 0)
            label_color = (0, 255, 0)
            defect_color = (0, 0, 255)
            cv2.rectangle(display, (x1, y1), (x2, y2), bottle_color, 3)
            bottle_cx = int((x1 + x2) / 2)
            bottle_cy = int((y1 + y2) / 2)
            orientation_data = track.get("orientation_data")
            if orientation_data is not None:
                render_orientation_axis(display, orientation_data, color=(0, 0, 255), thickness=3)
            live_label_box = match_label_to_bottle(track["box"], label_boxes)
            if live_label_box is not None:
                lx1, ly1, lx2, ly2 = map(int, live_label_box)
                cv2.rectangle(display, (lx1, ly1), (lx2, ly2), label_color, 3)
                cv2.putText(display, "LABEL", (lx1, max(20, ly1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, label_color, 2, cv2.LINE_AA)
                label_cx = int((lx1 + lx2) / 2)
                label_cy = int((ly1 + ly2) / 2)
                cv2.drawMarker(display, (label_cx, label_cy), label_color, cv2.MARKER_CROSS, 22, 2)
                cv2.line(display, (bottle_cx, bottle_cy), (label_cx, bottle_cy), (0, 0, 255), 3, cv2.LINE_AA)
                cv2.line(display, (label_cx, bottle_cy), (label_cx, label_cy), (0, 0, 255), 3, cv2.LINE_AA)
                cv2.line(display, (bottle_cx, bottle_cy), (label_cx, label_cy), (255, 255, 255), 1, cv2.LINE_AA)
            live_damage_boxes = [dmg for dmg in damage_boxes if dmg[0] >= x1 and dmg[2] <= x2 and dmg[1] >= y1 and dmg[3] <= y2]
            live_bump_boxes = [bump for bump in bump_boxes if bump[0] >= x1 and bump[2] <= x2 and bump[1] >= y1 and bump[3] <= y2]
            for defect_box in live_damage_boxes:
                dx1, dy1, dx2, dy2 = map(int, defect_box)
                cv2.rectangle(display, (dx1, dy1), (dx2, dy2), defect_color, 3)
                cv2.putText(display, "DAMAGE", (dx1, max(20, dy1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, defect_color, 2, cv2.LINE_AA)
            for defect_box in live_bump_boxes:
                bx1, by1, bx2, by2 = map(int, defect_box)
                cv2.rectangle(display, (bx1, by1), (bx2, by2), defect_color, 3)
                cv2.putText(display, "BUMP", (bx1, max(20, by1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, defect_color, 2, cv2.LINE_AA)
            live_orientation_angle = track["orientation_angle_history"][-1] if track.get("orientation_angle_history") else None
            live_h_value = abs(track["centricity_offset_history"][-1][0]) if track.get("centricity_offset_history") else None
            live_v_value = abs(track["centricity_offset_history"][-1][1]) if track.get("centricity_offset_history") else None
            orient_status = track.get("orientation")
            h_status = track.get("h_center")
            v_status = track.get("v_center")
            info_lines = [
                ("H offset: " + (format_measurement_text(live_h_value, h_status) if live_h_value is not None else (h_status or "Pending")), status_to_color(h_status)),
                ("V offset: " + (format_measurement_text(live_v_value, v_status) if live_v_value is not None else (v_status or "Pending")), status_to_color(v_status)),
                ("Tilt: " + (format_measurement_text(live_orientation_angle, orient_status, " deg") if live_orientation_angle is not None else (orient_status or "N/A")), status_to_color(orient_status)),
            ]
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 2
            line_height = 24
            text_block_h = line_height * len(info_lines) + 12
            text_block_w = 240
            text_x = x2 + 12
            if text_x + text_block_w > display.shape[1] - 5:
                text_x = max(5, x1 - text_block_w - 12)
            panel_bottom = 190
            text_y = max(panel_bottom if text_x < 320 else 20, min(y1 + 10, display.shape[0] - text_block_h - 5))
            overlay = display.copy()
            cv2.rectangle(overlay, (text_x - 6, text_y - 8), (text_x + text_block_w, text_y + text_block_h), (0, 0, 0), -1)
            display[:] = cv2.addWeighted(overlay, 0.55, display, 0.45, 0)
            for line_index, (line, color) in enumerate(info_lines):
                cv2.putText(display, line, (text_x, text_y + (line_index + 1) * line_height - 4), font, font_scale, color, thickness, cv2.LINE_AA)

        active_track = None
        for t in active_tracks:
            if t.get("missing", 0) == 0:
                active_track = t
                break
        label_pass = False
        bottle_ok = False
        bottle_detected = active_track is not None
        if active_track is not None:
            orient_ok = active_track.get("orientation") == "PASS"
            h_ok = active_track.get("h_center") == "PASS"
            v_ok = active_track.get("v_center") == "PASS"
            label_pass = orient_ok and h_ok and v_ok
            bottle_ok = label_pass and not bool(active_track.get("defects"))
        panel_pass = label_pass
        live_panel_capacity = active_track.get("capacity") if active_track is not None else None
        render_status_panel(
            display,
            total_bottles=total_bottles_completed,
            bottle_ok=bottle_ok,
            ok_bottles=total_bottles_ok,
            defective_bottles=total_bottles_defective,
            capacity=live_panel_capacity,
            label_pass=label_pass,
            panel_pass=panel_pass,
            start_x=10,
            start_y=10,
            bottle_detected=bottle_detected,
        )

        # ----- FPS + GPU/CPU overlay -----
        dt = time.perf_counter() - t0
        fps = 1.0 / dt if dt > 0 else 0.0
        gpu_util, mem_used, mem_total = query_gpu_stats()

        if PROFILE_ENABLED:
            profiler.add(
                capture_ms=max(0.0, (t0 - frame_loop_start) * 1000.0),
                preprocess_ms=(
                    detection_profile.get("preprocess_ms", 0.0)
                    + segmentation_profile.get("preprocess_ms", 0.0)
                ),
                detection_trt_ms=detection_profile.get("tensorrt_ms", 0.0),
                segmentation_trt_ms=segmentation_profile.get("tensorrt_ms", 0.0),
                gpu_post_ms=gpu_post_ms,
                cpu_post_ms=max(0.0, (time.perf_counter() - cpu_decode_end) * 1000.0),
                save_submit_ms=save_submit_ms,
                total_ms=dt * 1000.0,
                fps=fps,
            )
        cpu_util = psutil.cpu_percent(interval=None)

        display_fps = fps
       

        display_gpu = gpu_util
       

        display_cpu = cpu_util
       

        info = f"FPS: {display_fps:.1f} | GPU: {display_gpu}% | CPU: {display_cpu:.0f}%"
        (font_w, font_h), _ = cv2.getTextSize(info, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        x = display.shape[1] - font_w - 15
        y = display.shape[0] - 15
        cv2.rectangle(display, (x - 8, y - font_h - 8), (x + font_w + 8, y + 8), (0, 0, 0), -1)
        cv2.putText(display, info, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if video_writer is None:
            h_v, w_v = display.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, OUTPUT_VIDEO_FPS, (w_v, h_v))
        if video_writer is not None:
            video_writer.write(display)

        display_resized = cv2.resize(display, None, fx=0.33, fy=0.33, interpolation=cv2.INTER_AREA)
        cv2.imshow("Frosch Inference", display_resized)
        frame_total_time = time.perf_counter() - frame_loop_start
        current_frame_fps = 1.0 / max(frame_total_time, 1e-9)

        if bottle_boxes:
            bottle_fps_accumulator += current_frame_fps
            bottle_fps_sample_count += 1
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    for track in active_tracks:
        if not track["saved"] and track.get("best_complete_frame") is not None:
            if ready_to_persist_bottle(track, (0, 0), force=True):
                persist_bottle_images(track["best_complete_frame"], track)
    with open(JSON_LOG_PATH, "w") as jf:
        json.dump(bottle_result_records, jf, indent=2)
    print(f"Total Bottles: {total_bottles_completed}")
    print(f"Defective Bottles: {total_bottles_defective}")
    if bottle_fps_sample_count > 0:
        average_bottle_fps = bottle_fps_accumulator / bottle_fps_sample_count
        print(f"Average FPS (bottle detected only): {average_bottle_fps:.2f}")
    else:
        print("Average FPS (bottle detected only): N/A")

    if engine_fps_sample_count > 0:
        average_inference_fps = engine_fps_accumulator / engine_fps_sample_count
        print(f"Average inference FPS: {average_inference_fps:.2f}")
    if video_writer is not None:
        video_writer.release()
        video_writer = None
        print(f"Video saved: {OUTPUT_VIDEO_PATH}")
    if ia is not None:
        ia.stop()
    if h_cam is not None:
        h_cam.reset()
    try:
        pynvml.nvmlShutdown()
    except Exception:
        pass
    if PROFILE_ENABLED:
        profiler.report()
    _save_pool.shutdown(wait=True)
    cv2.destroyAllWindows()
