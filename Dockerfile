# QuantumTraderAI Dockerfile (corrected)
FROM python:3.11-slim

WORKDIR /app

COPY ./backend /app/backend
COPY ./backend/requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]