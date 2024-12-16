# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.conf.timezone = 'Asia/Tashkent'


app.conf.beat_schedule = {
    'send-notifications-everyday-8am': {
        'task': 'path.to.send_next_payment_notifications',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
    },
}
app.config_from_object('django.conf:settings', namespace='CELERY')

# app.autodiscover_tasks(['tg_bot.state.sent_notification'])
app.autodiscover_tasks()
