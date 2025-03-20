from celery import Celery
from src.config import Config

celery_app = Celery(
    "worker",
    broker=Config.CELERY_BROKER_URL,  # Redis URL
    backend=Config.CELERY_RESULT_BACKEND,  # Redis URL
)

celery_app.conf.update(
    result_expires=3600,  # Task results expire after 1 hour
)