from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from fatwas.models import Publication


@receiver([post_save, post_delete], sender=Publication)
def clear_publication_cache(sender, **kwargs):
    cache.clear()
