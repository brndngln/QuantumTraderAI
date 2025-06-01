# Use an official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in stages
COPY requirements.txt .

# First install basic Python packages
RUN pip install --no-cache-dir \
    fastapi uvicorn numpy pandas scipy matplotlib seaborn \
    python-dotenv pydantic sentry-sdk pytest pytest-cov black isort mypy

# Then install data science packages
RUN pip install --no-cache-dir \
    ta ccxt ray pyarrow numba scikit-learn xgboost lightgbm \
    torch transformers quantstats pyfolio optuna

# Then install database and cloud packages
RUN pip install --no-cache-dir \
    tensorflow-cpu keras pymongo redis aioredis boto3 mplfinance \
    nltk spacy tweepy alpha-vantage python-binance web3 pillow

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set permissions
RUN chmod +x /app/backend/main.py

# Expose ports
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"] \
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