FROM python:3.9-slim AS base

# Common dependencies
FROM base AS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
FROM dependencies AS python-deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# API Gateway
FROM python-deps AS api_gateway
WORKDIR /app
COPY backend/gateway/ .
COPY backend/utils/ ./utils/
COPY backend/monitoring/ ./monitoring/
COPY backend/security/ ./security/
COPY backend/service_mesh/ ./service_mesh/
EXPOSE 8000
CMD ["uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]

# Service Mesh
FROM python-deps AS service_mesh
WORKDIR /app
COPY backend/service_mesh/ .
COPY backend/utils/ ./utils/
COPY backend/monitoring/ ./monitoring/
COPY backend/security/ ./security/
EXPOSE 8000
CMD ["python", "service_mesh.py"]

# Visualization
FROM python-deps AS visualization
WORKDIR /app
COPY backend/visualization/ .
COPY backend/utils/ ./utils/
COPY backend/monitoring/ ./monitoring/
EXPOSE 8080
CMD ["python", "visualization.py"]
