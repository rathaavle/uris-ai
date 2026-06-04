# URIS-AI — FastAPI + React Static Files
# Target: GCP Cloud Run (asia-southeast1)
# PyMySQL is pure Python — no gcc/libmysqlclient needed
FROM python:3.12-slim

# Only curl needed for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (includes React build at src/uris_ai/static/)
COPY src/ ./src/

# Environment
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Shell form so $PORT is expanded at runtime
CMD python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1
