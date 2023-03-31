import os
from blogs_api.config.celery import *
import dotenv

dotenv.load_dotenv()

env = os.environ["ENV"]


if env == 'prod':
    from blogs_api.config.prod import *
else:
    from blogs_api.config.dev import *

