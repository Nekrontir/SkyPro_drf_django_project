import os
from celery import app as celery_app
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from .celery import app

__all__ = ('celery_app',)