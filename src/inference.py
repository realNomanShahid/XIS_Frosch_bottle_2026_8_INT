
import re

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import tensorrt as trt
import supervision as sv


# ----------------------------------------------------------------------
# Device setup
# ----------------------------------------------------------------------
COMPUTE_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if COMPUTE_DEVICE.type != "cuda":
    raise RuntimeError("This pipeline requires CUDA/TensorRT GPU execution.")

print(f"[OPT] Using device: {COMPUTE_DEVICE}")

# Flipped on from live_inference.py once CLI args are parsed; gates the
# per-engine GPU timing events recorded inside TRTVisionEngine.
PROFILE_ENABLED = False


def configure_profiling(enabled):
    """Enable/disable per-engine GPU timing from outside this module."""
    global PROFILE_ENABLED
    PROFILE_ENABLED = bool(enabled)
    if PROFILE_ENABLED:
        print("[OPT] Lightweight profiling: enabled")


# ----------------------------------------------------------------------
# Model / class configuration
# ----------------------------------------------------------------------
LEGACY_DETECTION_CHECKPOINT = "runs/frosch_medium/checkpoint_best_regular.pth"
LEGACY_SEGMENTATION_CHECKPOINT = "runs/frosch_seg_medium/checkpoint_best_total.pth"

DETECTION_ENGINE_PATH = "output/rfdetr-medium.trt"
SEGMENTATION_ENGINE_PATH = "output/rfdetr-seg-medium.trt"

SEGMENTATION_SCORE_THRESHOLD = 0.30

CLASS_CONFIDENCE_THRESHOLDS = {
    "bottle":   0.70,
    "label":    0.35,
    "capacity": 0.35,
    "bump":     0.50,
    "damage":   0.30,
    "scratch":  0.30,
}

BOTTLE_LABEL_NAME = "bottle"
MAX_ALLOWED_TILT_DEG = 45.0

DEFECT_OVERLAP_THRESH = 0.3

CLASS_NAMES = [
    "Frosch-bottle-UTNY-aUbJ-XBXs",
    "bottle",
    "bump",
    "capacity",
    "damage",
    "label",
    "scratch",
]

# ----------------------------------------------------------------------
# OCR / capacity-crop configuration
# ----------------------------------------------------------------------
CAPACITY_CROP_PAD_FRAC = 0.60
CAPACITY_CROP_PAD_PX = 25
OCR_MIN_CROP_SIDE = 300
KNOWN_CAPACITIES_ML = {100, 300, 500}

# Kept for parity with the original tuning knob; the live loop drives its
# own OCR cadence directly.
OCR_EVERY_N_FRAMES = 15
OCR_MIN_CONF = 0.18

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

# Per-frame CUDA mask cache so repeated orientation/centroid/overlap look-ups
# against the same NumPy mask don't repeatedly round-trip through the GPU.
_FRAME_MASK_CACHE = {}


def reset_frame_mask_cache():
    """Drop cached CUDA copies of this frame's masks; call once per frame."""
    _FRAME_MASK_CACHE.clear()


def as_cuda_mask(mask, device=COMPUTE_DEVICE):
    """Return a boolean CUDA tensor for `mask`, reusing a cached copy when possible."""
    if mask is None:
        return None
    if isinstance(mask, torch.Tensor):
        if mask.device == device and mask.dtype == torch.bool:
            return mask
        return mask.to(device=device, dtype=torch.bool, non_blocking=True)

    key = id(mask)
    cached = _FRAME_MASK_CACHE.get(key)
    if cached is not None and cached[0] is mask:
        return cached[1]

    cpu_mask = np.asarray(mask, dtype=np.bool_)
    tensor = torch.from_numpy(cpu_mask).to(
        device=device, dtype=torch.bool, non_blocking=False
    )
    _FRAME_MASK_CACHE[key] = (mask, tensor)
    return tensor


def compute_mask_orientation(mask):
    """GPU-accelerated PCA orientation of a mask, with a single scalar D2H sync."""
    if mask is None:
        return None
    try:
        m = as_cuda_mask(mask)
        ys, xs = torch.where(m)
        if xs.numel() < 20:
            return None

        points = torch.stack((xs.float(), ys.float()), dim=1)
        center = points.mean(dim=0)
        centered = points - center
        cov = (centered.T @ centered) / max(1, points.shape[0] - 1)

        eigenvalues, eigenvectors = torch.linalg.eigh(cov)
        major = eigenvectors[:, torch.argmax(eigenvalues)]
        norm = torch.linalg.vector_norm(major).clamp_min(1e-6)
        major = major / norm
        # Resolve the eigenvector sign without an intermediate host sync.
        sign = torch.where(major[1] < 0, major.new_tensor(-1.0), major.new_tensor(1.0))
        major = major * sign
        minor = torch.stack((-major[1], major[0]))
        angle = torch.rad2deg(torch.atan2(torch.abs(major[0]), torch.abs(major[1])))
        projections = centered @ major
        half_length = torch.maximum(
            projections.abs().max(), major.new_tensor(20.0)
        )

        summary = torch.stack(
            (
                center[0],
                center[1],
                major[0],
                major[1],
                minor[0],
                minor[1],
                angle,
                half_length,
            )
        )
        values = summary.detach().cpu().tolist()
        (cx, cy, dx, dy, mx, my, angle_deg, half_length_value) = values
        status = "PASS" if angle_deg <= MAX_ALLOWED_TILT_DEG else "FAIL"

        # Contour drawing stays on CPU; reuse the original NumPy mask when available.
        if isinstance(mask, torch.Tensor):
            mask_u8 = mask.detach().to(device="cpu", dtype=torch.uint8).numpy() * 255
        else:
            mask_u8 = np.asarray(mask, dtype=np.uint8) * 255

        contours, _ = cv2.findContours(
            mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        mask_contour = None
        if contours:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) >= 20:
                mask_contour = c.reshape(-1, 2).tolist()

        return {
            "status": status,
            "angle_deg": float(angle_deg),
            "center": (float(cx), float(cy)),
            "major": (float(dx), float(dy)),
            "minor": (float(mx), float(my)),
            "half_length": float(half_length_value),
            "mask_contour": mask_contour,
        }
    except Exception:
        return compute_mask_orientation_cpu_fallback(mask)


def compute_mask_orientation_cpu_fallback(mask):
    """CPU PCA fallback used if the CUDA path above raises."""
    if mask is None:
        return None
    mask_u8 = mask.astype(np.uint8) * 255
    ys, xs = np.where(mask_u8 > 0)
    if len(xs) < 20:
        return None
    points = np.column_stack((xs, ys)).astype(np.float32)
    center = points.mean(axis=0)
    centered = points - center
    covariance = np.cov(centered, rowvar=False)
    if covariance.shape != (2, 2) or not np.all(np.isfinite(covariance)):
        return None
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    major = eigenvectors[:, int(np.argmax(eigenvalues))].astype(np.float32)
    norm = float(np.linalg.norm(major))
    if norm < 1e-6:
        return None
    major /= norm
    if major[1] < 0:
        major = -major
    minor = np.array([-major[1], major[0]], dtype=np.float32)
    angle_deg = float(np.degrees(np.arctan2(abs(float(major[0])), abs(float(major[1])))))
    status = "PASS" if angle_deg <= MAX_ALLOWED_TILT_DEG else "FAIL"
    projections = centered @ major
    half_length = max(20.0, float(np.max(np.abs(projections))))
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_contour = None
    if contours:
        mask_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(mask_contour) < 20:
            mask_contour = None
    return {
        "status": status,
        "angle_deg": angle_deg,
        "center": (float(center[0]), float(center[1])),
        "major": (float(major[0]), float(major[1])),
        "minor": (float(minor[0]), float(minor[1])),
        "half_length": half_length,
        "mask_contour": mask_contour.reshape(-1, 2).tolist() if mask_contour is not None else None,
    }


def compute_mask_centroid(mask):
    """Centroid (x, y) of a boolean mask, computed on GPU when possible."""
    if mask is None:
        return None
    try:
        m = as_cuda_mask(mask)
        ys, xs = torch.where(m)
        if xs.numel() == 0:
            return None
        center = torch.stack((xs.float().mean(), ys.float().mean()))
        cx, cy = center.detach().cpu().tolist()
        return (float(cx), float(cy))
    except Exception:
        ys, xs = np.where(mask > 0)
        if len(xs) == 0:
            return None
        return (float(xs.mean()), float(ys.mean()))


def boxes_overlap_mask(defect_boxes, bottle_mask):
    """For each box, whether its overlap ratio with `bottle_mask` clears the defect threshold."""
    if not defect_boxes:
        return []
    if bottle_mask is None:
        return [False] * len(defect_boxes)

    try:
        m = as_cuda_mask(bottle_mask)
        ratios = []
        mh, mw = m.shape
        for defect_box in defect_boxes:
            dx1, dy1, dx2, dy2 = [int(v) for v in defect_box]
            dx1 = max(0, dx1)
            dy1 = max(0, dy1)
            dx2 = min(mw, dx2)
            dy2 = min(mh, dy2)
            if dx2 <= dx1 or dy2 <= dy1:
                ratios.append(m.new_tensor(0.0))
                continue
            roi = m[dy1:dy2, dx1:dx2]
            ratios.append(roi.float().mean())

        ratio_values = torch.stack(ratios).detach().cpu().tolist()
        return [float(v) >= DEFECT_OVERLAP_THRESH for v in ratio_values]
    except Exception:
        results = []
        for defect_box in defect_boxes:
            dx1, dy1, dx2, dy2 = [int(v) for v in defect_box]
            mh, mw = bottle_mask.shape[:2]
            dx1 = max(0, dx1)
            dy1 = max(0, dy1)
            dx2 = min(mw, dx2)
            dy2 = min(mh, dy2)
            if dx2 <= dx1 or dy2 <= dy1:
                results.append(False)
                continue
            roi = bottle_mask[dy1:dy2, dx1:dx2]
            overlap_ratio = float(roi.sum()) / max(1, roi.size)
            results.append(overlap_ratio >= DEFECT_OVERLAP_THRESH)
        return results


def box_overlaps_mask(defect_box, bottle_mask):
    """Single-box convenience wrapper around boxes_overlap_mask."""
    return boxes_overlap_mask([defect_box], bottle_mask)[0]


def box_iou(box_a, box_b):
    """Standard IoU between two (x1, y1, x2, y2) boxes."""
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    if inter == 0:
        return 0
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / float(area_a + area_b - inter)


def scale_mask_to_frame(mask, frame):
    """Resize a mask (nearest-neighbour) to match the given frame's dimensions."""
    if mask is None:
        return None
    fh, fw = frame.shape[:2]
    mh, mw = mask.shape[:2]
    if (mh, mw) == (fh, fw):
        return mask
    resized = cv2.resize(mask.astype(np.uint8), (fw, fh), interpolation=cv2.INTER_NEAREST)
    return resized.astype(bool)


def clip_mask_to_box(mask, box):
    """Zero out everything in `mask` outside of `box`."""
    if mask is None:
        return None
    x1, y1, x2, y2 = [int(v) for v in box]
    mh, mw = mask.shape[:2]
    x1 = max(0, x1); y1 = max(0, y1)
    x2 = min(mw, x2); y2 = min(mh, y2)
    constrained = np.zeros_like(mask)
    if x2 > x1 and y2 > y1:
        constrained[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
    return constrained


def select_bottle_mask(bottle_box, segmentation_detections):
    """Pick the segmentation mask whose 'bottle' box best overlaps `bottle_box`."""
    if segmentation_detections is None or segmentation_detections.mask is None:
        return None
    best_mask = None
    best_score = 0.0
    class_names = segmentation_detections.data.get("class_name", [])
    for i, cls in enumerate(class_names):
        if cls != BOTTLE_LABEL_NAME:
            continue
        if float(segmentation_detections.confidence[i]) < CLASS_CONFIDENCE_THRESHOLDS.get(BOTTLE_LABEL_NAME, SEGMENTATION_SCORE_THRESHOLD):
            continue
        seg_box = tuple(map(int, segmentation_detections.xyxy[i]))
        score = box_iou(bottle_box, seg_box)
        if score > best_score:
            best_score = score
            best_mask = segmentation_detections.mask[i]
    return best_mask


def select_label_mask(bottle_box, seg_detections, frame):
    """Pick and crop the best-matching 'label' mask for a given bottle box."""
    if seg_detections is None or seg_detections.mask is None:
        return None
    best_mask, best_score = None, 0.0
    for i, cls in enumerate(seg_detections.data.get("class_name", [])):
        if cls != "label":
            continue
        if float(seg_detections.confidence[i]) < CLASS_CONFIDENCE_THRESHOLDS.get("label", SEGMENTATION_SCORE_THRESHOLD):
            continue
        score = box_iou(bottle_box, tuple(map(int, seg_detections.xyxy[i])))
        if score > best_score:
            best_score = score
            best_mask = seg_detections.mask[i]
    if best_mask is None:
        return None
    best_mask = scale_mask_to_frame(best_mask, frame)
    return clip_mask_to_box(best_mask, bottle_box)


# ----------------------------------------------------------------------
# OCR
# ----------------------------------------------------------------------
def normalize_crop_for_ocr(bgr):
    """Lightweight GPU-friendly contrast normalization applied before OCR."""
    if bgr is None or bgr.size == 0:
        return bgr
    try:
        t = torch.from_numpy(bgr).to(COMPUTE_DEVICE, non_blocking=True).float() / 255.0
        y = 0.299 * t[..., 2] + 0.587 * t[..., 1] + 0.114 * t[..., 0]
        y_min, y_max = y.min(), y.max()
        if (y_max - y_min) > 1e-3:
            y = (y - y_min) / (y_max - y_min)
        t[..., 0] = t[..., 0] * 0.55 + y * 0.45
        t[..., 1] = t[..., 1] * 0.55 + y * 0.45
        t[..., 2] = t[..., 2] * 0.55 + y * 0.45
        return (t.clamp(0, 1) * 255).byte().cpu().numpy()
    except Exception:
        # Classic CLAHE fallback.
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def pad_capacity_box(box, img_w, img_h,
                      pad_frac=CAPACITY_CROP_PAD_FRAC,
                      pad_px=CAPACITY_CROP_PAD_PX):
    """Expand a capacity-marking box so OCR gets some surrounding context."""
    x1, y1, x2, y2 = [int(v) for v in box]
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    pad_x = int(bw * pad_frac) + pad_px
    pad_y = int(bh * pad_frac) + pad_px
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(img_w, x2 + pad_x)
    y2 = min(img_h, y2 + pad_y)
    return x1, y1, x2, y2


class PaddleCapacityReader:
    """Reads a known bottle capacity (100/300/500 ml) out of a crop via PaddleOCR."""

    def __init__(self, gpu=True, lang="en"):
        """Load PaddleOCR once, on GPU when available."""
        from paddleocr import PaddleOCR

        self.gpu = gpu and torch.cuda.is_available()
        self.lang = lang
        self.ocr = PaddleOCR(
            lang=lang,
            device="gpu" if self.gpu else "cpu",
            use_textline_orientation=True,
        )
        print(f"[OCR] Using PaddleOCR on {'GPU' if self.gpu else 'CPU'}")

    def read_capacity(self, crop_bgr):
        """Return (capacity_ml, avg_confidence) or (None, 0.0) if nothing usable was read."""
        if crop_bgr is None or crop_bgr.size == 0:
            return None, 0.0

        h, w = crop_bgr.shape[:2]
        short_side = min(h, w)
        if 0 < short_side < OCR_MIN_CROP_SIDE:
            scale = OCR_MIN_CROP_SIDE / short_side
            crop_bgr = cv2.resize(
                crop_bgr,
                (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_CUBIC,
            )

        crop_bgr = normalize_crop_for_ocr(crop_bgr)

        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        result = self.ocr.predict(rgb)
        if not result:
            return None, 0.0

        texts, scores = [], []
        for page in result:
            texts.extend(page.get("rec_texts", []))
            scores.extend(page.get("rec_scores", []))

        if not texts:
            return None, 0.0

        combined = " ".join(t.strip() for t in texts)
        avg_conf = sum(scores) / len(scores) if scores else 0.0
        return self._extract_capacity(combined, avg_conf)

    def _extract_capacity(self, combined_text, avg_conf):
        """Pull the best known-capacity number out of the recognized text."""
        candidates = re.findall(r"\d{2,4}", combined_text)
        if not candidates:
            return None, 0.0

        known_matches = [c for c in candidates if int(c) in KNOWN_CAPACITIES_ML]
        if not known_matches:
            return None, 0.0

        best = max(known_matches, key=lambda x: (len(x), int(x)))
        return int(best), avg_conf


# ----------------------------------------------------------------------
# TensorRT execution
# ----------------------------------------------------------------------
class PinnedFrameStager:
    """Reusable pinned-host RGB staging buffer shared by both TensorRT engines."""

    def __init__(self):
        self.tensor = None
        self.shape = None

    def stage(self, frame):
        """Convert a BGR frame to RGB and copy it into a pinned host tensor."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        shape = (h, w, 3)
        if self.tensor is None or self.shape != shape:
            self.tensor = torch.empty(
                shape,
                dtype=torch.uint8,
                pin_memory=True,
            )
            self.shape = shape
        source = torch.from_numpy(np.ascontiguousarray(rgb))
        self.tensor.copy_(source)
        return self.tensor


_FRAME_STAGER = PinnedFrameStager()


class TRTVisionEngine:
    """
    Persistent TensorRT runner with its own dedicated CUDA stream.

    The stream owns the whole per-frame GPU sequence: pinned host RGB ->
    device staging -> preprocessing -> TensorRT -> device-to-host output
    copy. Input/output buffers are allocated once and reused across frames,
    and no per-inference default-stream sync is performed.
    """

    def __init__(self, engine_path):
        """Load the serialized TensorRT engine and set up its buffers/stream."""
        self.engine_path = engine_path

        with open(engine_path, "rb") as f:
            runtime = trt.Runtime(TRT_LOGGER)
            self.engine = runtime.deserialize_cuda_engine(f.read())

        if self.engine is None:
            raise RuntimeError(f"Failed to load TensorRT engine: {engine_path}")

        self.context = self.engine.create_execution_context()
        if self.context is None:
            raise RuntimeError(f"Failed to create TensorRT context: {engine_path}")

        # One persistent, non-default CUDA stream per engine instance.
        self.stream = torch.cuda.Stream(device="cuda")
        self.input_name = None
        self.output_names = []

        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self.input_name = name
            else:
                self.output_names.append(name)

        shape = tuple(self.engine.get_tensor_shape(self.input_name))
        if len(shape) != 4 or shape[0] != 1 or shape[1] != 3:
            raise RuntimeError(f"Unexpected input shape: {shape}")
        if any(int(d) < 0 for d in shape):
            raise RuntimeError(f"Dynamic input shape is unsupported: {shape}")

        self.input_h = int(shape[2])
        self.input_w = int(shape[3])

        self._gpu_rgb_u8 = None
        self._gpu_input = torch.empty(
            (1, 3, self.input_h, self.input_w),
            dtype=torch.float32,
            device="cuda",
        )

        self._gpu_outputs = {}
        self._host_outputs = {}
        self._output_numpy_views = {}
        self._allocate_output_buffers()

        # Per-frame timing events; inert unless profiling is enabled.
        self._profile_start = torch.cuda.Event(enable_timing=True)
        self._profile_pre_end = torch.cuda.Event(enable_timing=True)
        self._profile_trt_start = torch.cuda.Event(enable_timing=True)
        self._profile_trt_end = torch.cuda.Event(enable_timing=True)
        self._profile_copy_end = torch.cuda.Event(enable_timing=True)

        self._pending = False
        self._last_frame_shape = None
        self._last_error = None

        self.context.set_tensor_address(self.input_name, self._gpu_input.data_ptr())
        for name, out in self._gpu_outputs.items():
            self.context.set_tensor_address(name, out.data_ptr())

        print(
            f"[OPTIMIZATION] TensorRT loaded: {engine_path} | "
            f"input={self.input_h}x{self.input_w} | outputs={self.output_names} | "
            f"dedicated_stream={self.stream.cuda_stream}"
        )

    @staticmethod
    def _dtype_for_trt(np_dtype):
        """Map a TensorRT-reported NumPy dtype onto the matching torch dtype."""
        if np_dtype == np.float32:
            return torch.float32
        if np_dtype == np.float16:
            return torch.float16
        if np_dtype == np.int32:
            return torch.int32
        if np_dtype == np.int64:
            return torch.int64
        raise RuntimeError(f"Unsupported TensorRT output dtype: {np_dtype}")

    def _allocate_output_buffers(self):
        """Allocate the persistent device + pinned-host buffers for every output tensor."""
        for name in self.output_names:
            shape = tuple(self.engine.get_tensor_shape(name))
            if any(int(d) < 0 for d in shape):
                raise RuntimeError(
                    f"Dynamic output shape is unsupported: {name} {shape}"
                )

            trt_dtype = trt.nptype(self.engine.get_tensor_dtype(name))
            torch_dtype = self._dtype_for_trt(trt_dtype)
            gpu_out = torch.empty(shape, dtype=torch_dtype, device="cuda")
            host_out = torch.empty(shape, dtype=torch_dtype, pin_memory=True)
            self._gpu_outputs[name] = gpu_out
            self._host_outputs[name] = host_out
            self._output_numpy_views[name] = host_out.numpy()

    def _ensure_gpu_rgb(self, rgb_host):
        """(Re)allocate the device RGB staging buffer if the frame shape changed."""
        if self._gpu_rgb_u8 is None or tuple(self._gpu_rgb_u8.shape) != tuple(rgb_host.shape):
            self._gpu_rgb_u8 = torch.empty(
                tuple(rgb_host.shape),
                dtype=torch.uint8,
                device="cuda",
            )

    def enqueue_rgb(self, rgb_host):
        """Enqueue one frame's preprocessing + inference without blocking the CPU."""
        if self._pending:
            raise RuntimeError(
                f"{self.engine_path}: previous inference is still pending. "
                "Call wait()/decode_current() before enqueueing another frame."
            )

        self._ensure_gpu_rgb(rgb_host)
        self._last_frame_shape = tuple(rgb_host.shape[:2])

        with torch.cuda.stream(self.stream):
            self._gpu_rgb_u8.copy_(rgb_host, non_blocking=True)

            if PROFILE_ENABLED:
                self._profile_start.record(self.stream)

            # uint8 HWC -> float32 CHW, resized and normalized on this engine's stream.
            normalized = self._gpu_rgb_u8.permute(2, 0, 1).unsqueeze(0).float()
            normalized = F.interpolate(
                normalized,
                size=(self.input_h, self.input_w),
                mode="bilinear",
                align_corners=False,
            )
            normalized.mul_(1.0 / 255.0)
            normalized[:, 0].sub_(0.485).div_(0.229)
            normalized[:, 1].sub_(0.456).div_(0.224)
            normalized[:, 2].sub_(0.406).div_(0.225)
            self._gpu_input.copy_(normalized)

            if PROFILE_ENABLED:
                self._profile_pre_end.record(self.stream)
                self._profile_trt_start.record(self.stream)

            if not self.context.execute_async_v3(self.stream.cuda_stream):
                raise RuntimeError(
                    f"TensorRT execution failed: {self.engine_path}"
                )

            if PROFILE_ENABLED:
                self._profile_trt_end.record(self.stream)

            # D2H copies happen asynchronously on the same stream into pinned buffers,
            # so the caller's single stream wait also covers these copies.
            for name, gpu_out in self._gpu_outputs.items():
                self._host_outputs[name].copy_(gpu_out, non_blocking=True)

            if PROFILE_ENABLED:
                self._profile_copy_end.record(self.stream)

        self._pending = True

    def wait(self):
        """Block until this engine's dedicated CUDA stream has drained."""
        if not self._pending:
            return
        self.stream.synchronize()
        self._pending = False

    def profile_ms(self):
        """Return this engine's last recorded stage timings in milliseconds."""
        if not PROFILE_ENABLED:
            return {}
        return {
            "preprocess_ms": self._profile_start.elapsed_time(self._profile_pre_end),
            "tensorrt_ms": self._profile_trt_start.elapsed_time(self._profile_trt_end),
            "output_copy_ms": self._profile_trt_end.elapsed_time(self._profile_copy_end),
            "gpu_total_ms": self._profile_start.elapsed_time(self._profile_copy_end),
        }

    def outputs_numpy(self):
        """Return the synchronized engine outputs as float32 NumPy arrays."""
        if self._pending:
            raise RuntimeError("Call wait() before outputs_numpy().")
        result = {}
        for name, host_out in self._host_outputs.items():
            result[name] = host_out.float().numpy()
        return result

    def decode_current(self, frame_shape, score_threshold, keep_masks=False):
        """Decode this engine's already-synchronized outputs into sv.Detections."""
        raw = self.outputs_numpy()
        return decode_detector_output(
            raw,
            frame_shape,
            score_threshold,
            keep_masks=keep_masks,
        )

    def infer(self, frame):
        """Blocking single-frame inference on this engine's dedicated stream."""
        rgb_host = _FRAME_STAGER.stage(frame)
        self.enqueue_rgb(rgb_host)
        self.wait()
        return self.outputs_numpy()


def logistic(x):
    """Numerically-safe sigmoid."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -88.0, 88.0)))


def decode_detector_output(raw, frame_shape, score_threshold, keep_masks=False):
    """Turn a raw RF-DETR dets/labels(/masks) dict into an sv.Detections object."""
    if "dets" not in raw or "labels" not in raw:
        raise RuntimeError(f"Expected dets/labels outputs, got {list(raw)}")

    boxes_cwh = raw["dets"][0]
    logits_all = raw["labels"][0]

    logits = logits_all[:, :-1]
    probs = logistic(logits)

    flat = probs.reshape(-1)
    k = min(boxes_cwh.shape[0], flat.size)
    order = np.argsort(-flat, kind="stable")[:k]

    scores = flat[order]
    num_classes = probs.shape[1]
    query_idx = order // num_classes
    class_ids = order % num_classes

    keep = scores > score_threshold
    scores = scores[keep]
    query_idx = query_idx[keep]
    class_ids = class_ids[keep]

    boxes = boxes_cwh[query_idx]
    h, w = frame_shape[:2]

    cx, cy, bw, bh = boxes.T
    xyxy = np.stack(
        [
            (cx - bw / 2) * w,
            (cy - bh / 2) * h,
            (cx + bw / 2) * w,
            (cy + bh / 2) * h,
        ],
        axis=1,
    )

    xyxy[:, [0, 2]] = np.clip(xyxy[:, [0, 2]], 0, w)
    xyxy[:, [1, 3]] = np.clip(xyxy[:, [1, 3]], 0, h)

    detections = sv.Detections(
        xyxy=xyxy.astype(np.float32),
        confidence=scores.astype(np.float32),
        class_id=class_ids.astype(int),
    )

    detections.data["class_name"] = np.array(
        [
            CLASS_NAMES[int(cid)] if int(cid) < len(CLASS_NAMES)
            else f"class_{int(cid)}"
            for cid in class_ids
        ],
        dtype=object,
    )

    detections.data["_rfdetr_query_idx"] = query_idx.astype(np.int32)

    if keep_masks and "masks" in raw:
        raw_masks = raw["masks"][0]
        selected_masks = raw_masks[query_idx]

        mask_tensor = torch.from_numpy(selected_masks).float().unsqueeze(1)
        mask_tensor = torch.nn.functional.interpolate(
            mask_tensor,
            size=(h, w),
            mode="bilinear",
            align_corners=False,
        ).squeeze(1)

        selected_masks_full = (mask_tensor.sigmoid() > 0.5).cpu().numpy()
        detections.mask = selected_masks_full

    return detections


def run_single_engine_inference(runtime_model, frame, threshold, keep_masks=False):
    """Blocking single-engine predict + decode; kept for parity, unused by the live loop."""
    raw = runtime_model.infer(frame)
    return decode_detector_output(
        raw,
        frame.shape,
        threshold,
        keep_masks=keep_masks,
    )


class BottlePipeline:
    """Bundles the detection engine, segmentation engine, and OCR reader."""

    def __init__(self, ocr_gpu=True):
        """Load both TensorRT engines and the PaddleOCR reader."""
        self.reader = PaddleCapacityReader(gpu=ocr_gpu)
        self.detector = TRTVisionEngine(DETECTION_ENGINE_PATH)
        self.segmenter = TRTVisionEngine(SEGMENTATION_ENGINE_PATH)
        print("[OPTIMIZATION] Native TensorRT backend: enabled for detection + segmentation.")

    def detect_and_segment(self, frame, detection_threshold=None, segmentation_threshold=None):
        """
        Run detection + segmentation without an intermediate sync. Each engine
        owns its own CUDA stream, so their preprocessing/inference work can
        overlap when the GPU has spare concurrency.
        """
        if detection_threshold is None:
            detection_threshold = min(CLASS_CONFIDENCE_THRESHOLDS.values())
        if segmentation_threshold is None:
            segmentation_threshold = min(CLASS_CONFIDENCE_THRESHOLDS.values())

        rgb_host = _FRAME_STAGER.stage(frame)

        self.detector.enqueue_rgb(rgb_host)
        self.segmenter.enqueue_rgb(rgb_host)

        # One wait per owning stream; no global CUDA-device barrier.
        self.detector.wait()
        self.segmenter.wait()

        detections = self.detector.decode_current(
            frame.shape,
            detection_threshold,
            keep_masks=False,
        )
        seg_detections = self.segmenter.decode_current(
            frame.shape,
            segmentation_threshold,
            keep_masks=True,
        )
        return detections, seg_detections

    def read_capacity_from_box(self, image, box):
        """Crop the padded capacity region out of `image` and OCR it."""
        h, w = image.shape[:2]
        x1, y1, x2, y2 = pad_capacity_box(box, w, h)
        crop = image[y1:y2, x1:x2]
        print(f"[OCR] crop={crop.shape} | box=({x1},{y1},{x2},{y2})")
        if crop.size == 0:
            return None, 0.0
        return self.reader.read_capacity(crop)
