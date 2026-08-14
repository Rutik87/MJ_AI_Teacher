# ==============================================================================
# MPSC AI Backend — Production Dockerfile
# Cloud-First High-Performance Architecture for FastAPI, RAG, and AI Agent
# ==============================================================================

FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Final Runtime Stage
# ==============================================================================
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies (Tesseract OCR for Marathi, ffmpeg for voice audio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-mar \
    tesseract-ocr-hin \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code
COPY . .

# Create persistent storage directories
RUN mkdir -p /app/data/uploads /app/data/embeddings /app/data/audio /app/data/db

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENVIRONMENT=production
ENV SUPABASE_CA_CERT_PATH=/app/certs/supabase-ca.crt

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Launch production server with Uvicorn / Gunicorn
CMD ["python", "run_backend.py"]
