import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "parking_ml",
    broker=redis_url,
    backend=redis_url,
)

app.conf.timezone = "Asia/Kolkata"

app.conf.beat_schedule = {

    "run-parking-analytics-every-hour": {
        "task": "scheduler.tasks.run_analytics",
        "schedule": 3600.0,
    },

}