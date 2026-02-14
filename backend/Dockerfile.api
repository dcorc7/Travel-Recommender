# FastAPI Backend Dockerfile for Hugging Face Spaces
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH="/app/src:/app/off_the_path" \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# System deps (curl for healthcheck; libgomp1 for xgboost runtime; build tools optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      libgomp1 \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml  README.md /app/

# Copy backend code (no ./backend/ prefix since we're already in backend/)
COPY ./src/ /app/src/
COPY ./configs/ /app/configs/
# COPY ./off_the_path/ /app/off_the_path/

# Install Python dependencies (including backend package)
RUN python -m pip install --upgrade pip wheel \
 && pip install .

# Create __init__.py to make api a proper Python package
RUN touch /app/src/api/__init__.py

# HuggingFace Spaces uses port 7860 by default
EXPOSE 7860

# Healthcheck (expects GET /health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Change working directory so that import paths work correctly
WORKDIR /app/src

# Start server on port 7860 for HuggingFace Spaces
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]