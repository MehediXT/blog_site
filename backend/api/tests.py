from django.test import SimpleTestCase, override_settings


class ProxySecurityTests(SimpleTestCase):
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_trusted_https_proxy_header_keeps_health_check_available(self):
        response = self.client.get(
            '/api/v1/health/', HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'no-store')

        insecure_response = self.client.get('/api/v1/health/')
        self.assertEqual(insecure_response.status_code, 301)
