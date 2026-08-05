from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(TimeStampMixin):
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name

class Posts(TimeStampMixin):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts', null=True, blank=True);
    staus = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='posts',null=True, blank=True)

    def __str__(self):
        return f"{self.category} - {self.title}"

class Comment(TimeStampMixin):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='comments', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    body = models.TextField()

    def __str__(self):
        return f"{self.author.first_name}-{self.post.title}"

    def __str__(self):
        return f"Comment by {self.author} on {self.post.title}"
# class Author(TimeStampMixin):
#     author_name = models.CharField(max_length=100)
#     authro_email = models.EmailField(unique=True)
#
#     def __str__(self):
#         return self.author_name
































































#hi
