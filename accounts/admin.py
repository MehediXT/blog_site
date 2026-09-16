from django.contrib import admin

from accounts.models import EmailVerificationToken, ScholarProfile, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_language', 'email_verified', 'email_updates')
    list_filter = ('preferred_language', 'email_verified')
    search_fields = ('user__username', 'user__email', 'display_name')


@admin.register(ScholarProfile)
class ScholarProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_status', 'is_suspended', 'institution')
    list_filter = ('verification_status', 'is_suspended')
    search_fields = ('user__username', 'user__email', 'institution')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'used_at')
