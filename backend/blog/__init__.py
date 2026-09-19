try:
    from .celery import app as celery_app
except ImportError:  # Celery is optional for the local Django-only workflow.
    celery_app = None

__all__ = ('celery_app',)
