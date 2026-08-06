from django.shortcuts import get_object_or_404, render
from posts.models import Posts


def post_list_view(request):
    posts = (
        query = request.GET.get('query', '')
        Posts.objects.filter(status='published')
        .select_related('category', 'author')
        .order_by('-created_at')
    )
    return render(request, 'post_list.html', {'posts': posts})


def post_detail_view(request, post_id):
    post = get_object_or_404(
        Posts.objects.select_related('category', 'author'),
        id=post_id,
        status='published',
    )
    return render(request, 'post_detail.html', {'post': post})
