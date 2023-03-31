import os

broker_url = os.environ.get("CELERY_BROKER_URL")
broker_api = os.environ.get("BROKER_API", broker_url)

BROKER_URL = broker_url

CELERY_BROKER_URL = BROKER_URL
CELERY_RESULT_BACKEND = BROKER_URL

worker_proc_alive_timeout = 12
