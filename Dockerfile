# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This line will copy app.py, pdf_processor.py, schemas/, and the new assets/ folder
COPY . .

EXPOSE 10000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]