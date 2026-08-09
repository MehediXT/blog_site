from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import FormMixin

from posts.forms import CommentForm, PostCreationForm
from posts.models import Category, Comment, Posts


class PostListView(ListView):
    model = Posts
    template_name = 'post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        self.query = self.request.GET.get('query', '').strip()
        self.category_id = self.request.GET.get('category_id', '')

        posts = (
            Posts.objects.filter(status='published')
            .select_related('category', 'author')
            .order_by('-created_at')
        )

        if self.query:
            posts = posts.filter(
                Q(title__icontains=self.query)
                | Q(content__icontains=self.query)
                | Q(references__icontains=self.query)
                | Q(author__username__icontains=self.query)
            )

        if self.category_id.isdigit():
            posts = posts.filter(category_id=self.category_id)

        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'categories': Category.objects.all(),
                'status_choices': Posts.STATUS_CHOICES,
                'query': self.query,
                'selected_category': self.category_id,
                'my_total': None,
                'my_categories': None,
                'result_count': context['posts'].count(),
            }
        )

        if self.request.user.is_authenticated:
            context['my_total'] = Posts.objects.filter(
                author=self.request.user
            ).count()
            context['my_categories'] = Category.objects.annotate(
                post_count=Count('posts')
            )

        return context


class PostDetailView(FormMixin, DetailView):
    model = Posts
    form_class = CommentForm
    template_name = 'post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Posts.objects.filter(status='published').select_related(
            'category',
            'author',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_comments'] = (
            self.object.comments.filter(parent__isnull=True)
            .select_related('author')
            .prefetch_related('replies__author')
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            return self.render_to_response(self.get_context_data())

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = self.object
        comment.author = self.request.user

        parent_id = self.request.POST.get('parent_id')
        if parent_id:
            comment.parent = get_object_or_404(
                Comment,
                id=parent_id,
                post=self.object,
            )

        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.id})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Posts
    form_class = PostCreationForm
    template_name = 'post_creation.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
