```Dockerfile
# QuantumTraderAI Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy backend folder into container
COPY ./backend /app/backend

# Copy the backend's requirements.txt
COPY ./backend/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Run the backend with Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]