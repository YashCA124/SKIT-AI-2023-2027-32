from celery import Celery
from celery.schedules import crontab

app = Celery(
    "parking_ml",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

app.conf.timezone = "Asia/Kolkata"

app.conf.beat_schedule = {

    "run-parking-analytics-every-hour": {
        "task": "scheduler.tasks.run_analytics",
        "schedule": 3600.0,
    },

}