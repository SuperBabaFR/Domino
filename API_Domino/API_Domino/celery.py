import os
from celery import Celery

# Définit le module Django par défaut pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'API_Domino.settings')

celery_app = Celery('API_Domino')

# Charge la configuration depuis settings.py
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover des tâches dans toutes les apps Django
celery_app.autodiscover_tasks()
