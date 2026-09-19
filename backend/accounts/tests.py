from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


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

