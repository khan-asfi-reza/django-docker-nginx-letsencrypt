from blogs_api.config.base import *

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STATIC_URL = f'https://{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_STATIC_LOCATION}/'

ALLOWED_HOSTS = [
    "app"
    # "https://sample.com",
    # "https://sample2.com",
]

CORS_ALLOW_ALL_ORIGINS = False

CORS_ORIGIN_WHITELIST = [
    # "https://sample.com",
    # "https://sample2.com",
]




