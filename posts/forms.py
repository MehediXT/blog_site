from django import forms

from posts.models import Comment, Posts


class PostCreationForm(forms.ModelForm):
    class Meta:
        model = Posts
        fields = ['title', 'content', 'category', 'status']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
