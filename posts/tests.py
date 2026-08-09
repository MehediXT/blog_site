from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

from posts.models import Category, Comment, Posts
from posts.views import PostCreateView, PostDetailView, PostListView


User = get_user_model()


class PublicPostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='SafePass123!')
        self.design_category = Category.objects.create(category_name='Design')
        self.culture_category = Category.objects.create(category_name='Culture')
        self.published_post = Posts.objects.create(
            title='Published story',
            content='This story is ready to read.',
            author=self.user,
            category=self.design_category,
            status='published',
        )
        self.draft_post = Posts.objects.create(
            title='Private draft',
            content='This should not be public.',
            author=self.user,
            status='draft',
        )

    def test_search_filters_published_posts(self):
        Posts.objects.create(
            title='A culture story',
            content='A different topic.',
            author=self.user,
            category=self.culture_category,
            status='published',
        )

        response = self.client.get(
            reverse('post-list'),
            {'query': 'ready'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search fatwas')
        self.assertContains(response, self.published_post.title)
        self.assertNotContains(response, 'A culture story')
        self.assertEqual(response.context['result_count'], 1)

    def test_post_urls_resolve_to_class_based_views(self):
        view_cases = (
            (reverse('post-list'), PostListView),
            (
                reverse('post_detail', args=[self.published_post.id]),
                PostDetailView,
            ),
            (reverse('create_post_view'), PostCreateView),
        )

        for url, view_class in view_cases:
            with self.subTest(url=url):
                self.assertIs(resolve(url).func.view_class, view_class)

    def test_category_filter_returns_matching_published_posts(self):
        culture_post = Posts.objects.create(
            title='A culture story',
            content='A different topic.',
            author=self.user,
            category=self.culture_category,
            status='published',
        )

        response = self.client.get(
            reverse('post-list'),
            {'category_id': self.culture_category.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, culture_post.title)
        self.assertContains(
            response,
            f'value="{self.culture_category.id}" selected',
        )
        self.assertNotContains(response, self.published_post.title)
        self.assertEqual(response.context['result_count'], 1)

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

    def test_logged_in_user_can_create_a_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('create_post_view'))

        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('create_post_view'),
            {
                'title': 'A new story',
                'content': 'This is a new story.',
                'references': 'https://example.com/trusted-source',
                'status': 'published',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        post = Posts.objects.get(
            title='A new story',
            author=self.user,
            status='published',
        )
        self.assertEqual(
            post.references,
            'https://example.com/trusted-source',
        )

        response = self.client.get(reverse('post_detail', args=[post.id]))
        self.assertContains(response, 'References')
        self.assertContains(response, 'https://example.com/trusted-source')

    def test_logged_in_user_can_add_a_comment(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('post_detail', args=[self.published_post.id]),
            {'body': 'This is a helpful comment.'},
        )

        self.assertRedirects(
            response,
            reverse('post_detail', args=[self.published_post.id]),
        )
        self.assertTrue(
            Comment.objects.filter(
                post=self.published_post,
                author=self.user,
                body='This is a helpful comment.',
            ).exists()
        )

        response = self.client.get(
            reverse('post_detail', args=[self.published_post.id])
        )

        self.assertContains(response, 'This is a helpful comment.')
