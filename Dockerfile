# Multi-stage build for security and size optimization

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    wheel \
    setuptools

# Copy requirements and install dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Production stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV LOG_LEVEL=info
ENV PORT=8000
ENV HOST=0.0.0.0

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R nobody:nogroup /app/data /app/logs

# Set user to non-root
USER nobody

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "$HOST", "--port", "$PORT", "--log-level", "$LOG_LEVEL", "--workers", "1"]