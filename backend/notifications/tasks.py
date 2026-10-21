from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from notifications.models import DeliveryOutbox

try:
    from celery import shared_task
except ImportError:  # pragma: no cover - dependency is installed by production images.
    def shared_task(*args, **kwargs):
        def decorator(function):
            return function
        return decorator


@shared_task
def deliver_pending_notifications():
    due_ids = list(
        DeliveryOutbox.objects.filter(status='pending')
        .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=timezone.now()))
        .order_by('id').values_list('id', flat=True)[:100]
    )
    for outbox_id in due_ids:
        deliver_pending_notification.delay(outbox_id)
    return len(due_ids)


@shared_task
def deliver_pending_notification(outbox_id):
    # Hold a row lock during SMTP delivery so overlapping workers cannot send
    # the same pending message. The periodic scan recovers work after a restart.
    with transaction.atomic():
        outbox = DeliveryOutbox.objects.select_for_update().select_related(
            'notification'
        ).get(pk=outbox_id)
        if outbox.status != 'pending':
            return outbox.status
        if outbox.next_attempt_at and outbox.next_attempt_at > timezone.now():
            return 'not_due'
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
            outbox.status = 'failed' if outbox.attempts >= 5 else 'pending'
            outbox.next_attempt_at = timezone.now() + timedelta(
                seconds=min(3600, 2 ** outbox.attempts * 60)
            )
            outbox.save(update_fields=[
                'attempts', 'last_error', 'status', 'next_attempt_at',
            ])
            return outbox.status
        outbox.status = 'sent'
        outbox.sent_at = timezone.now()
        outbox.attempts += 1
        outbox.last_error = ''
        outbox.save(update_fields=['status', 'sent_at', 'attempts', 'last_error'])
        return 'sent'
