FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Celery worker + beat scheduler. Redis is the broker (see REDIS_URL).
CMD ["celery", "-A", "scheduler.celery_app", "worker", "--beat", "--loglevel=info"]
