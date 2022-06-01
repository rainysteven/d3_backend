from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'd3_bakcend.settings')
app = Celery('d3_bakcend', backend='redis://:123456@localhost:6379/3')
app.config_from_object('d3_bakcend.celery.celeryConfig')
app.autodiscover_tasks()
