from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import ScholarProfile, UserProfile
from fatwas.models import Publication
from questions.models import Question


User = get_user_model()


class QuestionWorkflowApiTests(TestCase):
    def setUp(self):
        self.asker = User.objects.create_user(username='asker', password='SafePass123!', email='asker@example.com')
        UserProfile.objects.filter(user=self.asker).update(email_verified=True)
        self.scholar = User.objects.create_user(username='scholar', password='SafePass123!')
        self.reviewer = User.objects.create_user(username='reviewer', password='SafePass123!')
        for user in (self.scholar, self.reviewer):
            ScholarProfile.objects.create(user=user, verification_status='approved', public_bio='Verified scholar')
        self.moderator = User.objects.create_user(username='moderator', password='SafePass123!', is_staff=True)

    def _create_and_submit(self):
        self.client.force_login(self.asker)
        response = self.client.post('/api/v1/me/questions/', data={
            'title': 'Can I combine prayers while travelling?',
            'body': 'Please explain the ruling with evidence.',
            'language': 'en',
        }, content_type='application/json')
        question_id = response.json()['question']['id']
        self.client.post(f'/api/v1/me/questions/{question_id}/', data={
            'action': 'submit',
            'is_public': True,
            'public_title': 'Combining prayers while travelling',
            'public_body': 'What is the guidance on combining prayers while travelling?',
        }, content_type='application/json')
        return question_id

    def test_unverified_user_cannot_submit(self):
        user = User.objects.create_user(username='new-user', password='SafePass123!', email='new@example.com')
        self.client.force_login(user)
        created = self.client.post('/api/v1/me/questions/', data={'title': 'A question', 'body': 'Details', 'language': 'bn'}, content_type='application/json')
        response = self.client.post(f"/api/v1/me/questions/{created.json()['question']['id']}/", data={'action': 'submit'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error']['code'], 'email_unverified')

    def test_independent_review_releases_only_redacted_public_content(self):
        question_id = self._create_and_submit()
        self.client.force_login(self.moderator)
        response = self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.scholar)
        response = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={'body': 'The reviewed answer.', 'action': 'submit_for_review', 'language': 'en'}, content_type='application/json')
        revision_id = response.json()['revision_id']
        self.client.force_login(self.reviewer)
        response = self.client.post(f'/api/v1/reviews/{revision_id}/approve/', data={}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/v1/fatwas/')
        self.assertEqual(response.status_code, 200)
        public_data = response.json()['results'][0]
        self.assertEqual(public_data['title'], 'Combining prayers while travelling')
        self.assertNotIn('asker', response.content.decode())
        self.assertTrue(Publication.objects.filter(visibility='public').exists())

    def test_reviewer_cannot_be_the_assigned_scholar(self):
        question_id = self._create_and_submit()
        self.client.force_login(self.moderator)
        response = self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={'scholar_id': self.scholar.id, 'reviewer_id': self.scholar.id}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_unassigned_scholar_cannot_read_private_question(self):
        question_id = self._create_and_submit()
        other = User.objects.create_user(username='other-scholar', password='SafePass123!')
        ScholarProfile.objects.create(user=other, verification_status='approved')
        self.client.force_login(other)
        response = self.client.get(f'/api/v1/me/questions/{question_id}/')
        self.assertEqual(response.status_code, 404)
