# Multi-stage build
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install base packages
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .

# Stage 2: Production environment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy wheel files from builder
COPY --from=builder /wheels /wheels

# Install packages from wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.4.2 \
    python-dotenv==1.0.0 \
    redis==5.0.1 \
    aioredis==2.2.5 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV LOG_LEVEL=info

# Create necessary directories
RUN mkdir -p /app/data /app/logs
RUN chmod 755 /app/data /app/logs

# Set permissions
RUN chmod +x /app/backend/main.py

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"] \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY ./backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY ./backend /app

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]