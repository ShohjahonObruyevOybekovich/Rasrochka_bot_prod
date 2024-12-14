# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.conf.timezone = 'Asia/Tashkent'

app.config_from_object('django.conf:settings', namespace='CELERY')

# app.autodiscover_tasks(['tg_bot.state.sent_notification'])
app.autodiscover_tasks()
