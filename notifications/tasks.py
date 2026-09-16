from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from notifications.models import DeliveryOutbox

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - dependency is installed by production images.
    def shared_task(*args, **kwargs):
        def decorator(function):
            return function
        return decorator


@shared_task(bind=True, max_retries=5)
def deliver_pending_notification(self, outbox_id):
    outbox = DeliveryOutbox.objects.select_related('notification').get(pk=outbox_id)
    if outbox.status == 'sent':
        return 'already_sent'
    try:
        send_mail(
            outbox.notification.title,
            'You have a new update in Universe of Ilm. Sign in to view it.',
            settings.DEFAULT_FROM_EMAIL,
            [outbox.recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        outbox.attempts += 1
        outbox.last_error = str(exc)[:1000]
        outbox.next_attempt_at = timezone.now()
        outbox.save(update_fields=['attempts', 'last_error', 'next_attempt_at'])
        raise self.retry(exc=exc, countdown=min(3600, 2 ** outbox.attempts * 60))
    outbox.status = 'sent'
    outbox.sent_at = timezone.now()
    outbox.attempts += 1
    outbox.save(update_fields=['status', 'sent_at', 'attempts'])
    return 'sent'
