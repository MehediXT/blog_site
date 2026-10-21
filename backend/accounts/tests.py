from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import EmailVerificationToken, ScholarProfile, UserProfile


User = get_user_model()


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.password = 'SafePass123!'
        self.user = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password=self.password,
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post('/api/v1/auth/token/', {
            'username': 'reader',
            'password': self.password,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_email_can_be_used_to_login(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'READER@example.com',
            'password': self.password,
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_me_requires_jwt(self):
        response = self.client.get('/api/v1/me/')
        self.assertEqual(response.status_code, 401)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_expired_verification_link_can_be_replaced(self):
        old = EmailVerificationToken.objects.create(user=self.user, token='old-token')
        EmailVerificationToken.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=3)
        )
        self.assertEqual(self.client.get(
            '/api/v1/auth/verify-email/old-token/'
        ).status_code, 400)
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/v1/auth/resend-verification/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['sent'])
        self.assertEqual(len(mail.outbox), 1)
        new_token = EmailVerificationToken.objects.filter(user=self.user).exclude(pk=old.pk).get()
        self.assertEqual(self.client.get(
            f'/api/v1/auth/verify-email/{new_token.token}/'
        ).status_code, 200)
        self.assertTrue(UserProfile.objects.get(user=self.user).email_verified)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_changes_password_and_revokes_refresh_token(self):
        old_refresh = str(RefreshToken.for_user(self.user))
        requested = self.client.post('/api/v1/auth/password-reset/', {
            'email': self.user.email,
        }, format='json')
        self.assertEqual(requested.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        link = mail.outbox[0].body.split()[-1]
        params = parse_qs(urlparse(link).query)
        confirmed = self.client.post('/api/v1/auth/password-reset/confirm/', {
            'uid': params['reset_uid'][0],
            'token': params['reset_token'][0],
            'password': 'NewSafePass456!',
        }, format='json')
        self.assertEqual(confirmed.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSafePass456!'))
        self.assertEqual(self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': old_refresh,
        }, format='json').status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/password-reset/confirm/', {
            'uid': params['reset_uid'][0],
            'token': params['reset_token'][0],
            'password': 'AnotherPass789!',
        }, format='json').status_code, 400)


class ScholarApplicationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='SafePass123!',
        )
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={'email_verified': True},
        )
        self.payload = {
            'institution': 'Darul Ilm Institute',
            'biography': 'I have studied Islamic law for eight years.',
            'public_bio': 'A student and teacher of Islamic law.',
            'qualifications': 'Alimiyyah; BA in Islamic Studies',
            'specialties': ['Fiqh', 'Family matters'],
            'languages': ['bn', 'en'],
            'verification_status': 'approved',
        }

    def test_authenticated_user_can_submit_pending_scholar_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            '/api/v1/me/scholar-profile/', self.payload, format='json'
        )

        self.assertEqual(response.status_code, 201)
        scholar = ScholarProfile.objects.get(user=self.user)
        self.assertEqual(scholar.verification_status, 'pending')
        self.assertEqual(scholar.supported_languages, ['bn', 'en'])
        self.assertFalse(response.data['scholar_profile']['can_author'])

    def test_unverified_user_cannot_apply(self):
        UserProfile.objects.filter(user=self.user).update(email_verified=False)
        self.client.force_authenticate(self.user)
        response = self.client.post(
            '/api/v1/me/scholar-profile/', self.payload, format='json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'email_unverified')
        self.assertFalse(ScholarProfile.objects.filter(user=self.user).exists())

    def test_editing_approved_profile_requires_verification_again(self):
        ScholarProfile.objects.create(
            user=self.user,
            institution='Old Institute',
            biography='Old private biography',
            public_bio='Old public biography',
            qualifications='Old qualification',
            specialties=['Fiqh'],
            supported_languages=['en'],
            verification_status='approved',
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(
            '/api/v1/me/scholar-profile/', self.payload, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['scholar_profile']['verification_status'], 'pending')
        self.assertNotIn('verification_note', response.data['scholar_profile'])
