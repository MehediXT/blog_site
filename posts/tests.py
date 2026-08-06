from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Posts


User = get_user_model()


class PublicPostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='SafePass123!')
        self.published_post = Posts.objects.create(
            title='Published story',
            content='This story is ready to read.',
            author=self.user,
            status='published',
        )
        self.draft_post = Posts.objects.create(
            title='Private draft',
            content='This should not be public.',
            author=self.user,
            status='draft',
        )

    def test_list_shows_published_posts_only(self):
        response = self.client.get(reverse('post-list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_post.title)
        self.assertNotContains(response, self.draft_post.title)

    def test_detail_shows_published_post(self):
        response = self.client.get(
            reverse('post_detail', args=[self.published_post.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_post.content)

    def test_detail_hides_draft_posts(self):
        response = self.client.get(
            reverse('post_detail', args=[self.draft_post.id])
        )

        self.assertEqual(response.status_code, 404)
