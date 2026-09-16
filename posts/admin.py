from django.contrib import admin
from posts.models import Category, Posts, Comment

# Register your models here.
admin.site.register(Category)


@admin.register(Posts)
class LegacyPostsAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'content')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class LegacyCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    readonly_fields = ('post', 'author', 'parent', 'body', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
