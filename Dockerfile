# QuantumTraderAI Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy backend code
COPY backend /app/backend

# Copy requirements separately so they get cached
COPY backend/requirements.txt /app/requirements.txt

# Install pip and fix build tools
RUN apt-get update && apt-get install -y build-essential

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# Start backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]