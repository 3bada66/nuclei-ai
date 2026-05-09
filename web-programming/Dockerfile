# syntax=docker/dockerfile:1
# ── Backend production image for Fly.io ──────────────────────────────────────
# Run context: web-programming/ directory
# App is launched as:  uvicorn backend.main:app --host 0.0.0.0 --port 8000

FROM python:3.12-slim

# System libs needed by opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer-cached unless requirements.txt changes)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application source
COPY backend/ ./backend/
# Copy only the two src helpers used by analysis_service (no torch dep at import time)
COPY src/infer.py src/batch_count_refined.py ./src/

# Persistent storage dirs (overridden by Fly volume mount at /app/backend/storage)
RUN mkdir -p backend/storage/uploads backend/storage/results outputs/checkpoints

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
