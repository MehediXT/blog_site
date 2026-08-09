from django.urls import path
from posts.views import PostCreateView, PostDetailView, PostListView

urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('post/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('create_post_view/', PostCreateView.as_view(), name='create_post_view'),
]
