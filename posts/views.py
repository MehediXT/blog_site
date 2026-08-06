from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostCreationForm
from posts.models import Category, Comment, Posts


def post_list_view(request):
    query = request.GET.get('query', '').strip()
    category_id = request.GET.get('category_id', '')

    posts = Posts.objects.filter(status='published')
    posts = posts.select_related('category', 'author').order_by('-created_at')

    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(author__username__icontains=query)
        )

    if category_id.isdigit():
        posts = posts.filter(category_id=category_id)

    my_total = None
    my_categories = None
    if request.user.is_authenticated:
        my_total = Posts.objects.filter(author=request.user).count()
        my_categories = Category.objects.annotate(post_count=Count('posts'))

    return render(
        request,
        'post_list.html',
        {
            'posts': posts,
            'categories': Category.objects.all(),
            'status_choices': Posts.STATUS_CHOICES,
            'query': query,
            'selected_category': category_id,
            'my_total': my_total,
            'my_categories': my_categories,
            'result_count': posts.count(),
        },
    )


def post_detail_view(request, post_id):
    post = get_object_or_404(
        Posts.objects.select_related('category', 'author'),
        id=post_id,
        status='published',
    )
    parent_comments = (
        post.comments.filter(parent__isnull=True)
        .select_related('author')
        .prefetch_related('replies__author')
    )

    form = CommentForm()
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(
                    Comment,
                    id=parent_id,
                    post=post,
                )

            comment.save()
            return redirect('post_detail', post_id=post.id)

    return render(
        request,
        'post_detail.html',
        {
            'post': post,
            'parent_comments': parent_comments,
            'form': form,
        },
    )


@login_required
def post_create_view(request):
    if request.method == 'POST':
        form = PostCreationForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('dashboard')
    else:
        form = PostCreationForm()

    return render(request, 'post_creation.html', {'form': form})
