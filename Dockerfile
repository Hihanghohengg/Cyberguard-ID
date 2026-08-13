# CyberGuard-ID — Production Dockerfile (Render.com optimized)
FROM python:3.10-slim

WORKDIR /app

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create required directories
RUN mkdir -p artifacts/reports artifacts/predictions artifacts/evaluations \
    artifacts/logs models data/raw data/processed data/sample

# Start server — PORT is set by Render at runtime
CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT} --workers 1
