import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blogs_api.settings")


app = Celery("blogs_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.task_default_queue = 'celery'
