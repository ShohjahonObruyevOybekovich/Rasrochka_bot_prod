from __future__ import absolute_import, unicode_literals

# This ensures the app is always imported when
# Django starts, so shared tasks are available.
from .celery import app as celery_app

all = ('celery_app',)