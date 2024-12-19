import os
from celery.schedules import crontab


from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")


app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.beat_schedule = {
    "run-daily-task": {
        "task": "data.logs.tasks.daily_task",
        "schedule": crontab(minute=30, hour=1),  # Run every day at 9:10 AM
    },
    # "run-hourly-task": {
    #    "task": "data.logs.tasks.mark_as_gone",
    #    # "schedule": crontab(minute=0),  # Run every hour at the 0th minute
    #    # "schedule": crontab(hour=20, minute=24),  # Run every hour at the 0th minute
    #    "schedule": 1,  # Run every hour at the 0th minute
    # },
}

# app.autodiscover_tasks(lambda: ["data"])