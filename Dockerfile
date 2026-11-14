FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (Poppler for PDF preview, Tesseract for OCR, curl for health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-tur \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source explicitly to prevent sensitive data leakage
COPY main.py ./
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/

# Ensure data directory exists and set up non-root user
RUN mkdir -p /app/veriler \
    && groupadd -g 1000 appuser && useradd -u 1000 -g appuser -d /app -s /bin/sh appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Container healthcheck using the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run entry point with dotenv loaded
CMD ["python", "main.py"]
