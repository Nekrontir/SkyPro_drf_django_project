import os
from celery import Cel
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.conf import settings

app = Cel('config')

# Настройка Redis из переменных окружения
app.conf.broker_url = os.getenv('REDIS_HOST', 'localhost') + ':' + os.getenv('REDIS_PORT', '6379') + '/' + os.getenv('REDIS_DB', '0')
app.conf.result_backend = os.getenv('REDIS_HOST', 'localhost') + ':' + os.getenv('REDIS_PORT', '6379') + '/' + os.getenv('REDIS_DB', '0')

# Настройки таймзона
app.conf.timezone = settings.TIME_ZONE
app.conf.enable_utc = True

# Автоматическая импорта задач из всех приложений
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)