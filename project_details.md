# Project Details — Current Codebase Analysis
> Project: AI-Based Cell Nuclei Segmentation & Counting (Nuclei MVP)
> Analyzed: 2026-05-06

---

## What the Project Does

This is an AI-powered microscopy image analysis system. A user uploads a histopathology image (slide of tissue), and the backend runs a U-Net deep learning model to:
1. Segment (outline) individual cell nuclei in the image
2. Count how many nuclei are present
3. Return three output images: the resized input, the binary mask, and an overlay

The project was originally an AI coursework (ENS 005), and now a FastAPI web backend has been added to expose it as an HTTP API.

---

## File Inventory

| File | Role |
|---|---|
| `backend/main.py` | FastAPI app — 3 routes |
| `backend/schemas.py` | Pydantic response models |
| `backend/services/analysis_service.py` | Core analysis logic — model loading, inference, file saving |
| `backend/services/__init__.py` | Empty package marker |
| `backend/__init__.py` | Empty package marker |
| `src/infer.py` | Original standalone inference script (used by service) |
| `src/batch_count_refined.py` | Batch evaluation script — also exports `count_nuclei_from_binary` |
| `src/train.py` | Model training script |
| `src/dataset.py` | PyTorch dataset loader |
| `src/postprocess.py` | Postprocessing utilities |
| `src/metrics.py` | Evaluation metrics |
| `src/*.py` (others) | Offline batch analysis scripts |
| `requirements.txt` | Full pip freeze of dev environment |
| `backend/storage/uploads/` | Saved input images (6 existing) |
| `backend/storage/results/` | Saved output images (18 existing — 3 per job) |

---

## Line-by-Line Analysis

---

### `backend/main.py`

```python
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.schemas import AnalysisResponse, HealthResponse
from backend.services import analysis_service
```
**Lines 1–14 — Imports.**
Standard FastAPI imports. `pathlib.Path` used for safe path construction. All imports are used. No issues here.

---

```python
app = FastAPI(title="Nuclei MVP API", version="0.1.0")
```
**Line 16 — App instantiation.**
Basic FastAPI app with a title and version. These appear in the Swagger UI at `/docs`. No issues.

---

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Lines 18–27 — CORS configuration.**
- Origins are restricted to localhost dev ports — correct for development.
- `allow_credentials=False` — correct since there's no auth yet.
- `allow_methods=["*"]` — too permissive. Should be `["GET", "POST"]` since only those methods are used.
- `allow_headers=["*"]` — too permissive. Should be `["Content-Type"]`.
- **Problem:** No production origin is listed. When deployed, the frontend URL must be added here.

---

```python
RESULT_DIR = Path(__file__).resolve().parent / "storage" / "results"
```
**Line 29 — Result directory path.**
Uses `Path(__file__).resolve()` — robust, works regardless of where the server is started from. Good pattern.

---

```python
@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**analysis_service.get_health())
```
**Lines 32–34 — Health endpoint.**
Returns model status: device (cpu/cuda), model loaded flag, mode (model/fallback-demo), and any load error. Useful for deployment monitoring. No issues.

---

```python
@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload.")
    try:
        result = analysis_service.analyze(payload, file.filename or "upload.png")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    return AnalysisResponse(**analysis_service.result_to_dict(result))
```
**Lines 37–50 — Main analyze endpoint.**

Good:
- `async def` — correct for I/O-bound route.
- Content-type checked before reading.
- Empty file check after reading.
- `ValueError` → 400, other exceptions → 500 — good error mapping.

**Problems:**
1. `file.content_type.startswith("image/")` — content-type is **client-supplied** and can be faked. A malicious file with `Content-Type: image/png` but real content as a script will pass this check. Real validation requires reading magic bytes (first few bytes of the file).
2. `await file.read()` loads the **entire file into memory first**, then the size check happens inside `analysis_service.analyze()`. A 500MB upload would be fully loaded into RAM before being rejected. The size check should happen at the route level using `file.size` or chunked reading.
3. No authentication — this heavy ML inference endpoint is completely open. Anyone can hammer it for free GPU/CPU usage.
4. No rate limiting — a single client can submit thousands of requests per minute.

---

```python
@app.get("/files/{filename}")
def get_file(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    target = RESULT_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(target)
```
**Lines 53–61 — File serving endpoint.**

Good:
- Path traversal guard checks for `/`, `\\`, `..` — catches most common attacks.
- `target.is_file()` check prevents directory traversal via symlinks.

**Problems:**
1. The traversal guard is manual string checking instead of using `Path.resolve()` + comparing to `RESULT_DIR`. The correct pattern is:
   ```python
   target = (RESULT_DIR / filename).resolve()
   if not str(target).startswith(str(RESULT_DIR.resolve())):
       raise HTTPException(status_code=400)
   ```
2. No `media_type` set on `FileResponse`. FastAPI infers from extension, but for `.png` files served to browsers this usually works. Minor issue.
3. No authentication — result files from other users' analyses are accessible if anyone knows or guesses the filename (12-character hex UUID, which is guessable with effort).

---

### `backend/schemas.py`

```python
class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
    mode: str = Field(description='"model" | "fallback-demo" | "uninitialised"')
    load_error: Optional[str] = None
```
**Lines 7–12 — HealthResponse.**

- `mode: str` — the description documents the allowed values but does not enforce them.
- **Problem:** Should use `Literal["model", "fallback-demo", "uninitialised"]` for type safety and OpenAPI documentation.
- `load_error: Optional[str] = None` — correct Pydantic v2 syntax.

---

```python
class AnalysisMetadata(BaseModel):
    original_filename: str
    mode: str
    threshold: Optional[float] = None
    min_area: int
    image_size: int
    processing_ms: int
    device: str
```
**Lines 15–22 — AnalysisMetadata.**

**Problems:**
1. `mode: str` — same as above, should be `Literal["model", "fallback-demo"]`.
2. `min_area: int` — no lower bound. Should be `Field(ge=1)`.
3. `processing_ms: int` — no lower bound. Should be `Field(ge=0)`.
4. `image_size: int` — always 256 in the service but no constraint expressed here.
5. `threshold: Optional[float] = None` — no range validation. Should be `Field(ge=0.0, le=1.0)` when present.

---

```python
class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str
    cell_count: int
    input_url: str
    mask_url: str
    overlay_url: str
    metadata: AnalysisMetadata
```
**Lines 25–34 — AnalysisResponse.**

**Problems:**
1. `cell_count: int` — no lower bound. Should be `Field(ge=0)`.
2. `status: str` — should be `Literal["ok", "ok-fallback"]`.
3. `input_url`, `mask_url`, `overlay_url` are relative paths (`/files/{name}`). They don't include the hostname. The frontend must prepend the API base URL manually — this is an implicit coupling that should be documented.
4. The `metadata: AnalysisMetadata` field is populated from `AnalysisResult.metadata`, which is a plain `dict` in the service. Pydantic v2 will coerce the dict to `AnalysisMetadata` automatically — this works but is fragile. If the dict keys ever diverge from the schema, a 422/500 error will occur at runtime.

---

### `backend/services/analysis_service.py`

```python
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
from src.infer import make_overlay
from src.batch_count_refined import count_nuclei_from_binary
```
**Lines 24–28 — sys.path manipulation and src imports.**

**Problems:**
1. `sys.path.append(str(ROOT))` mutates the Python module search path at import time. This is fragile — it depends on `ROOT` resolving to the project root correctly, which assumes a fixed directory layout. If the package is ever installed or run from a different structure, this breaks.
2. Both imports are at **module level**. If `src` is missing or has import errors, the entire `analysis_service` module fails to import — crashing the backend on startup, before any request is served.
3. The `# noqa: E402` comments suppress the linter warning about imports not being at the top of the file but don't fix the underlying fragility.

---

```python
_model = None
_device = None
_mode = "uninitialised"
_load_error: Optional[str] = None
```
**Lines 42–45 — Global mutable state.**

**Problems:**
1. These are module-level globals shared across all requests. FastAPI uses an async event loop with thread pool workers for blocking operations. Under concurrent load, multiple threads could simultaneously see `_mode == "uninitialised"` and both attempt to load the model — causing duplicate initialization, wasted memory, or a crash.
2. No locking mechanism (no `threading.Lock`, no `asyncio.Lock`).

---

```python
def _ensure_model_loaded() -> None:
    global _model, _device, _mode, _load_error
    if _mode != "uninitialised":
        return
    try:
        import torch
        import segmentation_models_pytorch as smp
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        model = smp.Unet(encoder_name="resnet18", encoder_weights=None,
                         in_channels=3, classes=1).to(_device)
        if not CHECKPOINT_PATH.exists():
            raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")
        state = torch.load(CHECKPOINT_PATH, map_location=_device)
        model.load_state_dict(state)
        model.eval()
        _model = model
        _mode = "model"
    except Exception as e:
        _load_error = f"{type(e).__name__}: {e}"
        _mode = "fallback-demo"
        _model = None
```
**Lines 60–85 — Lazy model loading.**

**Problems:**
1. **Not thread-safe** — the `if _mode != "uninitialised": return` check is not atomic. Under concurrent requests, two threads could both pass this check before either finishes loading.
2. **`torch.load` without `weights_only=True`** — In PyTorch 2.x, loading checkpoints without `weights_only=True` allows arbitrary Python objects to be deserialized from the `.pth` file (pickle-based). This is a known security vulnerability if the checkpoint file could ever be replaced. Should be:
   ```python
   state = torch.load(CHECKPOINT_PATH, map_location=_device, weights_only=True)
   ```
3. **Lazy loading** — model is loaded on the **first request**, not on startup. The first user gets a slow response (model loading can take 5–30 seconds). Should use FastAPI's `lifespan` context manager to load on startup.
4. **`except Exception` swallows all errors** — import errors, OOM errors, corrupted checkpoints all silently become `"fallback-demo"` mode. This makes debugging production issues very difficult.

---

```python
def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image. Supported formats: PNG, JPG, TIFF.")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(rgb, (IMAGE_SIZE, IMAGE_SIZE))
```
**Lines 99–106 — Image decoding.**

Good: `None` check after `cv2.imdecode` with a helpful error message. BGR→RGB conversion is correct.

**Minor issue:** `cv2.resize` uses `INTER_LINEAR` by default. For medical images, `INTER_AREA` (downscaling) or `INTER_CUBIC` (upscaling) might preserve more detail — but this is a domain concern, not a bug.

---

```python
def _predict_with_model(image_rgb: np.ndarray) -> np.ndarray:
    import torch
    tensor = image_rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = torch.tensor(tensor, dtype=torch.float32).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()
    return ((probs > THRESHOLD).astype(np.uint8)) * 255
```
**Lines 109–118 — U-Net inference.**

Good: `torch.no_grad()` context — correct, saves memory during inference. `sigmoid` converts raw logits to probabilities. Binary threshold at `THRESHOLD = 0.8`.

**Problems:**
1. `import torch` inside the function — redundant since torch is already conditionally imported in `_ensure_model_loaded`. Minor style issue.
2. If `_model` is somehow `None` when this function is called (race condition), it will raise `AttributeError: 'NoneType' object has no attribute '__call__'` — no guard here.

---

```python
def _predict_fallback(image_rgb: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
```
**Lines 121–127 — Fallback (Otsu threshold) demo path.**

Good: Inverted Otsu threshold + morphological opening to remove noise. Reasonable fallback for demo purposes.

**Note:** This path produces inaccurate counts (hence `used_min_area = 20` in the caller). This should be clearly communicated to the user — which it is via `status: "ok-fallback"` and the message string.

---

```python
def analyze(image_bytes: bytes, original_filename: str) -> AnalysisResult:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Upload exceeds {MAX_UPLOAD_BYTES} bytes.")
    ...
    upload_path = UPLOAD_DIR / f"{job_id}{suffix}"
    upload_path.write_bytes(image_bytes)
    ...
    cv2.imwrite(str(input_path), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
```
**Lines 130–189 — Main analyze function.**

**Problems:**
1. **Size check too late** — `len(image_bytes) > MAX_UPLOAD_BYTES` runs after the route has already read the full file with `await file.read()`. A 100MB upload is fully in RAM before this line executes.
2. **Files never cleaned up** — `upload_path.write_bytes(image_bytes)` and the three `cv2.imwrite` calls save files permanently. There is no cleanup job, no TTL, no disk space management. Over time (especially in production), this will fill the disk.
3. **Blocking I/O in async context** — `write_bytes()` and `cv2.imwrite()` are synchronous blocking calls. They are called from within an `async def` route handler via the service. This blocks the FastAPI event loop, preventing other requests from being served during the file write. Should use `asyncio.to_thread()`.
4. **`job_id = uuid.uuid4().hex[:12]`** — Only 12 hex characters = 48 bits of entropy. Not enough for a security-sensitive ID. For a non-security context (just a filename), it's acceptable, but collisions are possible after ~16 million jobs (birthday paradox at 2^24).
5. **`input_url = f"/files/{input_path.name}"`** — Relative URL. The frontend must know the API base URL to make this work. No absolute URL is provided.

---

### `src/infer.py` (imported by analysis_service)

```python
THRESHOLD = 0.5
...
model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
```
**Problems:**
1. **`THRESHOLD = 0.5`** — The original inference script uses 0.5 but the analysis service uses 0.8 (the calibrated threshold from XML ground-truth tuning). These constants are inconsistent. The service is correct, but the standalone script is stale.
2. **`torch.load` without `weights_only=True`** — Same security issue as in the service.
3. This file has a `main()` function designed to run standalone. It will **not** cause issues when imported since `if __name__ == "__main__"` guards the entry point — but the module-level constants (`CHECKPOINT_PATH`, `IMAGE_PATH`, `OUTPUT_DIR`) execute on import and will create the `outputs/inference/` directory even when called from the service.

---

### `src/batch_count_refined.py` (imported by analysis_service)

```python
def count_nuclei_from_binary(binary_mask: np.ndarray, min_area: int = 1) -> int:
    binary_mask = binary_mask.astype("uint8")
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    count = 0
    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            count += 1
    return count
```
**Lines 44–57 — The counting function (only part actually used by the service).**

Good: Correct connected-components algorithm. Skips background label (0). `min_area` filter removes noise.

**Problem:** When this file is imported, its module-level code runs:
```python
VAL_CSV = ROOT / "data/splits/all.csv"
GT_COUNTS_CSV = ROOT / "outputs/ground_truth/ground_truth_counts.csv"
CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PRED_MASK_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
```
This means importing `count_nuclei_from_binary` silently **creates 3 directories** on disk every time. It also defines `torch`, `smp`, `DataLoader`, `tqdm`, `pd` as module-level imports — all of which must succeed or the import fails.

---

### `requirements.txt`

**Problems:**
1. **UTF-16 encoded** — The file has a space between every character. `pip install -r requirements.txt` will fail. This needs to be re-saved as UTF-8 without BOM.
2. **Full environment dump** — Contains 90+ packages including Streamlit, matplotlib, scipy, scikit-learn, altair, etc. that are not used by the FastAPI backend. The actual backend needs only ~6 packages.
3. **`torch==2.10.0` included** — PyTorch is 2GB+. Including it in a web backend's requirements file means every deployment downloads 2GB. Torch should be a separate optional install.
4. **Both `opencv-python` and `opencv-python-headless` listed** — These conflict on servers (headless is the correct one for servers without a display). Only `opencv-python-headless` should be in the backend requirements.
5. **`fastapi` and `uvicorn` are present** but buried among 90 other packages with no separation.

---

## Problems Summary

### Critical (blocking course requirements)

| # | Problem | Impact |
|---|---|---|
| 1 | **No database** | Fails the "Database" and "Entities and relations" requirements entirely |
| 2 | **No authentication** | Fails "Basic Authentication + 2FA" requirement |
| 3 | **No frontend** | No React/Vite/HTML frontend exists anywhere in the repo |
| 4 | **No tests** | No pytest, no Playwright — fails testing requirements |
| 5 | **No user entities** | No User table, no roles, no admin dashboard |
| 6 | **No deployment config** | No Procfile, no Dockerfile, no fly.toml |

### Security Problems

| # | Problem | Risk |
|---|---|---|
| 7 | `torch.load` without `weights_only=True` | Arbitrary code execution via pickle if checkpoint is tampered |
| 8 | Content-type check is client-supplied | Non-image files can pass validation |
| 9 | Path traversal guard uses string matching not `resolve()` | Partial bypass possible |
| 10 | No authentication on `/api/analyze` | Anyone can use the GPU/CPU for free |
| 11 | No rate limiting | DoS via flooding the heavy ML endpoint |
| 12 | Result files accessible without auth | Users can access other users' results if they guess the filename |
| 13 | `allow_methods=["*"]`, `allow_headers=["*"]` | Overly permissive CORS |

### Performance / Reliability Problems

| # | Problem | Impact |
|---|---|---|
| 14 | Size check after `file.read()` loads full file | OOM on large uploads before rejection |
| 15 | Blocking I/O inside async route | Blocks event loop during file writes |
| 16 | Model loaded lazily on first request | First user gets 5–30 second timeout |
| 17 | No thread safety on model loading globals | Race condition under concurrent requests |
| 18 | Files never cleaned up | Disk fills indefinitely |

### Code Quality Problems

| # | Problem | File |
|---|---|---|
| 19 | `sys.path.append` at import time | `analysis_service.py` |
| 20 | Module-level imports from `src` crash backend on startup if src is missing | `analysis_service.py` |
| 21 | `except Exception` hides all model load errors | `analysis_service.py` |
| 22 | Importing `batch_count_refined` creates 3 directories silently | `batch_count_refined.py` |
| 23 | `THRESHOLD = 0.5` in `infer.py` vs `0.8` in service — inconsistent | `infer.py` |
| 24 | `mode: str` instead of `Literal[...]` — no value enforcement | `schemas.py` |
| 25 | No field constraints (`ge=0`) on numeric schema fields | `schemas.py` |
| 26 | `requirements.txt` is UTF-16 encoded — `pip install` will fail | `requirements.txt` |
| 27 | Both `opencv-python` and `opencv-python-headless` in requirements | `requirements.txt` |
| 28 | Relative URLs in `AnalysisResponse` — frontend must know API base | `analysis_service.py` |

---

## What Needs to Be Added for the Course (from PROJECT_PLAN.md)

Based on the grading requirements, the following must be built on top of this existing project:

### Must-Have (base grade)
- [ ] PostgreSQL database with SQLModel
- [ ] User entity with proper fields and relations to analysis jobs
- [ ] AnalysisJob entity (stores job_id, user_id FK, status, cell_count, timestamps)
- [ ] All Pydantic schemas separated from ORM models
- [ ] JWT authentication (register, login, protected routes)
- [ ] React + Vite frontend

### For Full Auth Points + Bonuses
- [ ] TOTP 2FA with pyotp (1st 2FA method — full points)
- [ ] Email OTP (2nd 2FA method — +5)
- [ ] Google OAuth (social login 1 — full points)
- [ ] GitHub OAuth (social login 2 — +5)
- [ ] Discord OAuth (social login 3 — +10)

### For Authorization Bonus (+10)
- [ ] `role` field on User: `admin`, `researcher`, `viewer`
- [ ] `require_role()` dependency
- [ ] Admin dashboard in frontend (user management, role editor)

### For Testing Bonus (+15)
- [ ] pytest unit tests for all endpoints
- [ ] Playwright E2E tests (90%+ coverage)
- [ ] GitHub Actions CI/CD (tests before deploy)

### For Deployment Bonus (+10)
- [ ] Dockerfile for backend
- [ ] Fly.io config (`fly.toml`)
- [ ] Cloudflare Pages config (`_headers`)

### Security (required, no bonus)
- [ ] Rate limiting on `/api/analyze`, `/auth/login`, `/auth/register`
- [ ] Fix `torch.load` → add `weights_only=True`
- [ ] Move size check to route level
- [ ] Tighten CORS
- [ ] Fix path traversal guard with `resolve()`
- [ ] Move model loading to FastAPI lifespan startup
- [ ] Add thread lock on model initialization
- [ ] Fix `requirements.txt` encoding and slim it down

---

## What Is Good and Can Be Kept

1. **The U-Net inference pipeline** — the AI logic in `analysis_service.py` is well-structured and works correctly (with the fallback path as a safety net).
2. **The fallback demo mode** — excellent UX decision. The app is testable without the GPU model.
3. **Path traversal guard on `/files/`** — the intent is correct, just needs the `resolve()` fix.
4. **Error mapping** — `ValueError` → 400, generic → 500 in `main.py` is clean.
5. **Idempotent directory creation** — `mkdir(parents=True, exist_ok=True)` is correct.
6. **`AnalysisResult` dataclass** — clean internal data structure, `asdict()` for serialization.
7. **`job_id` as filename prefix** — good namespacing for stored files.
8. **`mode` field in response** — frontend can tell users when they're getting fallback results.
