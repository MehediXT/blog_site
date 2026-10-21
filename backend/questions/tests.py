from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.models import ScholarProfile, UserProfile
from fatwas.models import Publication
from questions.models import Question


User = get_user_model()


class QuestionWorkflowApiTests(APITestCase):
    def setUp(self):
        self.asker = User.objects.create_user(username='asker', password='SafePass123!', email='asker@example.com')
        UserProfile.objects.filter(user=self.asker).update(email_verified=True)
        self.scholar = User.objects.create_user(username='scholar', password='SafePass123!')
        self.reviewer = User.objects.create_user(username='reviewer', password='SafePass123!')
        for user in (self.scholar, self.reviewer):
            ScholarProfile.objects.create(user=user, verification_status='approved', public_bio='Verified scholar')
        self.moderator = User.objects.create_user(username='moderator', password='SafePass123!', is_staff=True)

    def _create_and_submit(self):
        self.client.force_authenticate(self.asker)
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
        self.client.force_authenticate(user)
        created = self.client.post('/api/v1/me/questions/', data={'title': 'A question', 'body': 'Details', 'language': 'bn'}, content_type='application/json')
        response = self.client.post(f"/api/v1/me/questions/{created.json()['question']['id']}/", data={'action': 'submit'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'email_unverified')

    def test_independent_review_releases_only_redacted_public_content(self):
        question_id = self._create_and_submit()
        self.client.force_authenticate(self.moderator)
        response = self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.client.force_authenticate(self.scholar)
        response = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={'body': 'The reviewed answer.', 'action': 'submit_for_review', 'language': 'en'}, content_type='application/json')
        revision_id = response.json()['revision_id']
        self.client.force_authenticate(self.reviewer)
        response = self.client.post(f'/api/v1/reviews/{revision_id}/approve/', data={}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/v1/fatwas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'no-store')
        public_data = response.json()['results'][0]
        self.assertEqual(public_data['title'], 'Combining prayers while travelling')
        self.assertNotIn('asker', response.content.decode())
        self.assertTrue(Publication.objects.filter(visibility='public').exists())

        publication_id = public_data['id']
        self.client.force_authenticate(self.asker)
        report = self.client.post(f'/api/v1/fatwas/{publication_id}/report/', data={
            'reason': 'Please recheck the wording.',
        }, format='json')
        self.assertEqual(report.status_code, 201)
        self.assertEqual(self.client.get('/api/v1/moderation/reports/').status_code, 403)
        self.client.force_authenticate(self.moderator)
        queue = self.client.get('/api/v1/moderation/reports/')
        self.assertEqual(len(queue.data['results']), 1)
        action = self.client.post(
            f"/api/v1/moderation/reports/{report.data['report_id']}/",
            {'action': 'withdraw', 'note': 'Pending a new review.'}, format='json',
        )
        self.assertEqual(action.status_code, 200)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/fatwas/').data['count'], 0)

    def test_reviewer_cannot_be_the_assigned_scholar(self):
        question_id = self._create_and_submit()
        self.client.force_authenticate(self.moderator)
        response = self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={'scholar_id': self.scholar.id, 'reviewer_id': self.scholar.id}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_unassigned_scholar_cannot_read_private_question(self):
        question_id = self._create_and_submit()
        other = User.objects.create_user(username='other-scholar', password='SafePass123!')
        ScholarProfile.objects.create(user=other, verification_status='approved')
        self.client.force_authenticate(other)
        response = self.client.get(f'/api/v1/me/questions/{question_id}/')
        self.assertEqual(response.status_code, 404)

    def test_private_answer_is_visible_to_asker_only(self):
        question_id = self._create_and_submit()
        self.client.force_authenticate(self.asker)
        self.client.post(f'/api/v1/me/questions/{question_id}/', data={
            'action': 'change_consent', 'is_public': False,
        }, format='json')
        self.client.force_authenticate(self.moderator)
        self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={
            'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id,
        }, format='json')
        self.client.force_authenticate(self.scholar)
        answer = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={
            'body': 'Private scholarly answer.', 'action': 'submit_for_review',
            'language': 'en', 'references': ['Reference one'],
        }, format='json')
        self.client.force_authenticate(self.reviewer)
        review = self.client.post(f"/api/v1/reviews/{answer.data['revision_id']}/approve/", {}, format='json')
        self.assertEqual(review.status_code, 200)
        self.client.force_authenticate(self.asker)
        own = self.client.get(f'/api/v1/me/questions/{question_id}/')
        self.assertEqual(own.data['question']['approved_answer']['body'], 'Private scholarly answer.')
        self.assertEqual(own.data['question']['approved_answer']['references'], ['Reference one'])
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/fatwas/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/v1/me/questions/{question_id}/').status_code, 401)

    def test_withdrawn_question_cannot_be_approved(self):
        question_id = self._create_and_submit()
        self.client.force_authenticate(self.moderator)
        self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={
            'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id,
        }, format='json')
        self.client.force_authenticate(self.scholar)
        answer = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={
            'body': 'A pending answer.', 'action': 'submit_for_review', 'language': 'en',
        }, format='json')
        self.client.force_authenticate(self.asker)
        withdrawn = self.client.post(f'/api/v1/me/questions/{question_id}/', data={
            'action': 'withdraw',
        }, format='json')
        self.assertEqual(withdrawn.status_code, 200)
        self.client.force_authenticate(self.reviewer)
        review = self.client.post(f"/api/v1/reviews/{answer.data['revision_id']}/approve/", {}, format='json')
        self.assertEqual(review.status_code, 409)
        self.assertFalse(Publication.objects.filter(visibility='public').exists())

    def test_assigned_question_cannot_gain_public_consent(self):
        question_id = self._create_and_submit()
        self.client.force_authenticate(self.asker)
        self.client.post(f'/api/v1/me/questions/{question_id}/', data={
            'action': 'change_consent', 'is_public': False,
        }, format='json')
        self.client.force_authenticate(self.moderator)
        self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={
            'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id,
        }, format='json')
        self.client.force_authenticate(self.asker)
        response = self.client.post(f'/api/v1/me/questions/{question_id}/', data={
            'action': 'change_consent', 'is_public': True,
            'public_title': 'An unreviewed title', 'public_body': 'Unreviewed wording',
        }, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Question.objects.get(pk=question_id).is_public)

    def test_rejected_answer_can_be_reassigned(self):
        question_id = self._create_and_submit()
        replacement = User.objects.create_user(username='replacement', password='SafePass123!')
        ScholarProfile.objects.create(user=replacement, verification_status='approved')
        self.client.force_authenticate(self.moderator)
        self.client.post(f'/api/v1/moderation/questions/{question_id}/assign/', data={
            'scholar_id': self.scholar.id, 'reviewer_id': self.reviewer.id,
        }, format='json')
        self.client.force_authenticate(self.scholar)
        answer = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={
            'body': 'First answer.', 'action': 'submit_for_review', 'language': 'en',
        }, format='json')
        self.client.force_authenticate(self.reviewer)
        self.assertEqual(self.client.post(
            f"/api/v1/reviews/{answer.data['revision_id']}/reject/",
            {'feedback': 'Needs a different specialist.'}, format='json',
        ).status_code, 200)
        self.client.force_authenticate(self.scholar)
        self.assertEqual(self.client.get(f'/api/v1/me/questions/{question_id}/').status_code, 404)
        self.client.force_authenticate(self.moderator)
        self.assertEqual(self.client.post(
            f'/api/v1/moderation/questions/{question_id}/assign/',
            {'scholar_id': replacement.id, 'reviewer_id': self.reviewer.id}, format='json',
        ).status_code, 200)
        self.client.force_authenticate(replacement)
        revised = self.client.post(f'/api/v1/scholar/questions/{question_id}/answer/', data={
            'body': 'Replacement answer.', 'action': 'submit_for_review', 'language': 'en',
        }, format='json')
        self.assertEqual(revised.status_code, 201)
        self.assertNotEqual(revised.data['revision_id'], answer.data['revision_id'])
