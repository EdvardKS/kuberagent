FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# importante para logs en tiempo real
ENV PYTHONUNBUFFERED=1