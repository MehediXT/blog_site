from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    LANGUAGE_CHOICES = [('bn', 'Bangla'), ('en', 'English')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=150, blank=True)
    preferred_language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default='bn'
    )
    email_verified = models.BooleanField(default=False)
    email_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_username()


class ScholarProfile(models.Model):
    VERIFICATION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    biography = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    institution = models.CharField(max_length=200, blank=True)
    specialties = models.JSONField(default=list, blank=True)
    supported_languages = models.JSONField(default=list, blank=True)
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_CHOICES, default='pending'
    )
    verification_note = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_scholar_profiles',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    public_bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def can_author(self):
        return self.verification_status == 'approved' and not self.is_suspended

    def __str__(self):
        return f'Scholar profile: {self.user.get_username()}'


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'used_at'])]
