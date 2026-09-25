from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import ScholarProfile, UserProfile


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
