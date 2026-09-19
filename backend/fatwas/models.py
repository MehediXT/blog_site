from django.conf import settings
from django.db import models
import uuid


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name_en = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name_en',)

    def __str__(self):
        return self.name_en


class Methodology(models.Model):
    slug = models.SlugField(unique=True)
    name_en = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name_en',)

    def __str__(self):
        return self.name_en


class Answer(models.Model):
    question = models.OneToOneField(
        'questions.Question', on_delete=models.PROTECT, related_name='answer'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='authored_answers',
    )
    approved_revision = models.ForeignKey(
        'AnswerRevision',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AnswerRevision(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In review'),
        ('changes_requested', 'Changes requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    answer = models.ForeignKey(Answer, on_delete=models.PROTECT, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    language = models.CharField(max_length=2, choices=[('bn', 'Bangla'), ('en', 'English')])
    body = models.TextField()
    public_question_title = models.CharField(max_length=240, blank=True)
    public_question_body = models.TextField(blank=True)
    references = models.JSONField(default=list, blank=True)
    methodology = models.ForeignKey(
        Methodology, null=True, blank=True, on_delete=models.PROTECT, related_name='revisions'
    )
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='answer_revisions'
    )
    supersedes = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.PROTECT, related_name='corrections'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('answer', 'revision_number'), name='unique_answer_revision')
        ]
        ordering = ('-revision_number',)


class ReviewDecision(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('changes_requested', 'Changes requested'),
        ('rejected', 'Rejected'),
    ]

    revision = models.ForeignKey(AnswerRevision, on_delete=models.PROTECT, related_name='decisions')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='review_decisions'
    )
    decision = models.CharField(max_length=24, choices=DECISION_CHOICES)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Publication(models.Model):
    VISIBILITY_CHOICES = [('public', 'Public'), ('private', 'Private'), ('withdrawn', 'Withdrawn')]

    answer = models.OneToOneField(Answer, on_delete=models.PROTECT, related_name='publication')
    approved_revision = models.ForeignKey(AnswerRevision, on_delete=models.PROTECT)
    public_id = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    slug = models.SlugField(max_length=260, unique=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    published_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-published_at', '-id')


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'publication'), name='unique_user_bookmark')
        ]


class Report(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('resolved', 'Resolved'), ('dismissed', 'Dismissed')]

    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='reports')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=('object_type', 'object_id'))]
