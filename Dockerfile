# Use an official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install base packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.4.2 \
    python-dotenv==1.0.0 \
    redis==5.0.1 \
    aioredis==2.2.5 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6

# Install testing and development packages
RUN pip install --no-cache-dir \
    typing-extensions==4.5.0 \
    pytest==7.4.3 \
    black==23.11.0 \
    mypy==1.7.0

# Install monitoring and logging packages
RUN pip install --no-cache-dir \
    sentry-sdk==1.39.1 \
    structlog==23.2.0

# Install rate limiting and retrying packages
RUN pip install --no-cache-dir \
    ratelimit==3.0.1 \
    retrying==1.3.4

# Install data science packages
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    pandas==2.0.3 \
    matplotlib==3.7.2 \
    scipy==1.10.1 \
    seaborn==0.12.2

# Install machine learning packages
RUN pip install --no-cache-dir \
    tensorflow-cpu==2.13.0

# Install web and communication packages
RUN pip install --no-cache-dir \
    websockets==11.0.3 \
    python-telegram-bot==20.4 \
    requests==2.31.0

# Install caching and monitoring packages
RUN pip install --no-cache-dir \
    aiocache==0.11.1 \
    aiomcache==0.6.0 \
    opentelemetry-api==1.18.0 \
    opentelemetry-sdk==1.18.0 \
    opentelemetry-instrumentation-fastapi==0.40b0 \
    opentelemetry-instrumentation-requests==0.40b0 \
    opentelemetry-instrumentation-sqlalchemy==0.40b0 \
    jaeger-client==5.6.0

# Install system monitoring packages
RUN pip install --no-cache-dir \
    psutil==5.9.6

# Install performance optimization packages
RUN pip install --no-cache-dir \
    numba==0.57.1

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