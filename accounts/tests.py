from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Posts


User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = 'SafePass123!'
        self.user = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password=self.password,
        )

    def test_registration_logs_user_in_and_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-reader',
                'email': 'new-reader@example.com',
                'password1': self.password,
                'password2': self.password,
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue(User.objects.filter(username='new-reader').exists())

    def test_duplicate_email_is_rejected(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'another-reader',
                'email': 'READER@example.com',
                'password1': self.password,
                'password2': self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email already exists.')

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': self.password},
        )

        self.assertRedirects(response, reverse('dashboard'))

    def test_auth_templates_render(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)
        self.assertEqual(self.client.get(reverse('password_reset')).status_code, 200)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('password_change')).status_code, 200)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )

    def test_logout_uses_post_and_redirects_to_login(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_password_change_requires_authentication(self):
        response = self.client.get(reverse('password_change'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('password_change')}",
        )

    def test_dashboard_lists_only_the_logged_in_users_posts(self):
        own_post = Posts.objects.create(
            title='My story',
            content='A story from this user.',
            author=self.user,
            status='draft',
        )
        other_user = User.objects.create_user(username='other', password=self.password)
        Posts.objects.create(
            title='Someone else’s story',
            content='A different story.',
            author=other_user,
            status='draft',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, own_post.title)
        self.assertNotContains(response, 'Someone else’s story')
