from django.urls import path

from posts.views import post_create_view, post_detail_view, post_list_view

urlpatterns = [
    path('', post_list_view, name='post-list'),
    path('post/<int:post_id>/', post_detail_view, name='post_detail'),
    path('create_post_view/', post_create_view, name='create_post_view'),
]
