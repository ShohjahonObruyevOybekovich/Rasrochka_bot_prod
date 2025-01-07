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
        'schedule': crontab(hour=12, minute=3),
    },
    'send_daily_message-to-admin' : {
        'task': 'bot.tasks.send_daily_message_to_admin',
        'schedule': crontab(hour=12, minute=3),
    }
}

app.conf.timezone = "Asia/Tashkent"
