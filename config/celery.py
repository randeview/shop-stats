import logging.config
import os

from celery import Celery
from celery.signals import setup_logging
from django.apps import apps
from django.conf import settings
from kombu import Exchange, Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery_app = Celery("shop_stats")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

default_exchange = Exchange("shop_stats", type="direct")
default_queue = Queue("shop_stats", default_exchange, routing_key="shop_stats")
celery_app.conf.task_queues = (default_queue,)

celery_app.conf.task_default_queue = "shop_stats"
celery_app.conf.task_default_exchange = "shop_stats"
celery_app.conf.task_default_exchange_type = "direct"
celery_app.conf.task_default_routing_key = "shop_stats"
celery_app.conf.task_routes = {
    "celery.backend_cleanup": {"queue": "shop_stats"},
}


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Setup logging for celery."""
    logging.config.dictConfig(settings.LOGGING)
