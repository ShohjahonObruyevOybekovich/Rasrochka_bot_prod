import os
from celery.schedules import crontab


from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")


app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'send-daily-messages': {
        'task': 'bot.tasks.send_daily_message',
        'schedule': crontab(hour=19, minute=5),
    },
}

app.conf.timezone = "Asia/Tashkent"