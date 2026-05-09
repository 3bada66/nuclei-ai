"""Analysis service: wraps the existing U-Net inference + connected-component counter.

Reuses (does not copy):
- src.infer.make_overlay   — overlay rendering
- src.batch_count_refined.count_nuclei_from_binary — counting

If the checkpoint cannot be loaded (missing file, torch error, etc.) the service
falls back to an Otsu-threshold demo path so the UI is still testable end-to-end.
The real AI code in /src is never modified.
"""

from __future__ import annotations

import sys
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

# src.infer / src.batch_count_refined import torch at module level, which is only
# available in the full ML environment. When torch is absent the functions below
# are replaced with pure-OpenCV equivalents that are functionally identical.
try:
    from src.infer import make_overlay  # noqa: E402
    from src.batch_count_refined import count_nuclei_from_binary  # noqa: E402
except Exception:  # ImportError when torch / smp are not installed
    def make_overlay(image_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:  # type: ignore[misc]
        color_mask = np.zeros_like(image_rgb)
        color_mask[mask > 0] = [255, 0, 0]
        return cv2.addWeighted(image_rgb, 0.7, color_mask, 0.3, 0)

    def count_nuclei_from_binary(binary_mask: np.ndarray, min_area: int = 1) -> int:  # type: ignore[misc]
        bm = binary_mask.astype("uint8")
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(bm, connectivity=8)
        return sum(1 for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= min_area)

CHECKPOINT_PATH = ROOT / "outputs" / "checkpoints" / "best_model.pth"
UPLOAD_DIR = ROOT / "backend" / "storage" / "uploads"
RESULT_DIR = ROOT / "backend" / "storage" / "results"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
THRESHOLD = 0.8       # corrected operating point from batch_count_refined.py
MIN_AREA = 1
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Lazy singletons populated on first use
_model = None
_device = None
_mode = "uninitialised"  # "model" | "fallback-demo" | "uninitialised"
_load_error: Optional[str] = None


@dataclass
class AnalysisResult:
    job_id: str
    status: str
    message: str
    cell_count: int
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: dict


def _ensure_model_loaded() -> None:
    """Load the U-Net checkpoint once. On failure, switch to fallback-demo."""
    global _model, _device, _mode, _load_error
    if _mode != "uninitialised":
        return
    try:
        import torch
        import segmentation_models_pytorch as smp
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        model = smp.Unet(
            encoder_name="resnet18",
            encoder_weights=None,
            in_channels=3,
            classes=1,
        ).to(_device)
        if not CHECKPOINT_PATH.exists():
            raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")
        state = torch.load(CHECKPOINT_PATH, map_location=_device)
        model.load_state_dict(state)
        model.eval()
        _model = model
        _mode = "model"
    except Exception as e:  # noqa: BLE001
        _load_error = f"{type(e).__name__}: {e}"
        _mode = "fallback-demo"
        _model = None


def get_health() -> dict:
    _ensure_model_loaded()
    return {
        "status": "ok",
        "device": _device or "cpu",
        "model_loaded": _model is not None,
        "mode": _mode,
        "load_error": _load_error,
    }


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """bytes -> RGB uint8 image resized to IMAGE_SIZE x IMAGE_SIZE."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image. Supported formats: PNG, JPG, TIFF.")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))


def _predict_with_model(image_rgb: np.ndarray) -> np.ndarray:
    """Run U-Net on an RGB uint8 image. Returns binary mask {0,255}."""
    import torch
    tensor = image_rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = torch.tensor(tensor, dtype=torch.float32).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()
    return ((probs > THRESHOLD).astype(np.uint8)) * 255


def _predict_fallback(image_rgb: np.ndarray) -> np.ndarray:
    """Otsu-threshold demo path. Used only when the real model cannot load."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


def analyze(image_bytes: bytes, original_filename: str) -> AnalysisResult:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload exceeds {MAX_UPLOAD_BYTES} bytes.")

    _ensure_model_loaded()

    job_id = uuid.uuid4().hex[:12]
    suffix = Path(original_filename).suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        suffix = ".png"

    upload_path = UPLOAD_DIR / f"{job_id}{suffix}"
    upload_path.write_bytes(image_bytes)

    image_rgb = _decode_image(image_bytes)

    started = time.perf_counter()
    if _mode == "model":
        mask = _predict_with_model(image_rgb)
        used_min_area = MIN_AREA
    else:
        mask = _predict_fallback(image_rgb)
        used_min_area = 20  # demo path is noisier — drop tiny artefacts
    overlay = make_overlay(image_rgb, mask)
    cell_count = count_nuclei_from_binary(mask, min_area=used_min_area)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    input_path = RESULT_DIR / f"{job_id}_input.png"
    mask_path = RESULT_DIR / f"{job_id}_mask.png"
    overlay_path = RESULT_DIR / f"{job_id}_overlay.png"

    cv2.imwrite(str(input_path), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    status = "ok" if _mode == "model" else "ok-fallback"
    message = (
        "Analysis complete (U-Net inference)."
        if _mode == "model"
        else "Analysis complete (fallback demo mode — model checkpoint not available)."
    )

    return AnalysisResult(
        job_id=job_id,
        status=status,
        message=message,
        cell_count=int(cell_count),
        input_url=f"/files/{input_path.name}",
        mask_url=f"/files/{mask_path.name}",
        overlay_url=f"/files/{overlay_path.name}",
        metadata={
            "original_filename": original_filename,
            "mode": _mode,
            "threshold": THRESHOLD if _mode == "model" else None,
            "min_area": used_min_area,
            "image_size": IMAGE_SIZE,
            "processing_ms": elapsed_ms,
            "device": _device or "cpu",
        },
    )


def result_to_dict(r: AnalysisResult) -> dict:
    return asdict(r)
