# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy backend code and requirements
COPY ./backend ./backend
COPY ./backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r ./backend/requirements.txt

# Expose the app port (default FastAPI/uvicorn port)
EXPOSE 8000

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]