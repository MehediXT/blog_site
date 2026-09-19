from django.conf import settings
from django.db import models


class Question(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In progress'),
        ('needs_clarification', 'Needs clarification'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    LANGUAGE_CHOICES = [('bn', 'Bangla'), ('en', 'English'), ('ar', 'Arabic')]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='questions')
    original_title = models.CharField(max_length=240)
    original_body = models.TextField()
    public_title = models.CharField(max_length=240, blank=True)
    public_body = models.TextField(blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    category = models.ForeignKey(
        'fatwas.Category', null=True, blank=True, on_delete=models.PROTECT, related_name='questions'
    )
    madhhab_preference = models.CharField(max_length=120, blank=True)
    is_public = models.BooleanField(default=False)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='draft')
    assigned_scholar = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name='scholar_assignments'
    )
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name='review_assignments'
    )
    moderation_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('status', 'language')),
            models.Index(fields=('assigned_scholar', 'status')),
            models.Index(fields=('assigned_reviewer', 'status')),
        ]


class ClarificationMessage(models.Model):
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name='clarifications')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
