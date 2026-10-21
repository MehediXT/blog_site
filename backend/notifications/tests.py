from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from notifications.models import DeliveryOutbox, Notification
from notifications.tasks import deliver_pending_notification


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DeliveryOutboxTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username='recipient', email='recipient@example.com', password='SafePass123!'
        )
        notification = Notification.objects.create(
            user=user, kind='answer_released', title='Your answer is ready'
        )
        self.outbox = DeliveryOutbox.objects.create(
            notification=notification,
            recipient_email=user.email,
            idempotency_key=f'notification:{notification.pk}',
        )

    def test_message_is_sent_once(self):
        self.assertEqual(deliver_pending_notification.run(self.outbox.pk), 'sent')
        self.assertEqual(deliver_pending_notification.run(self.outbox.pk), 'sent')
        self.assertEqual(len(mail.outbox), 1)

    def test_failed_delivery_is_kept_for_retry(self):
        with patch('notifications.tasks.send_mail', side_effect=ConnectionError('offline')):
            self.assertEqual(deliver_pending_notification.run(self.outbox.pk), 'pending')
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.attempts, 1)
        self.assertIsNotNone(self.outbox.next_attempt_at)
