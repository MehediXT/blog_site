from django.shortcuts import render
from posts.models import Posts

#
# class PostListView:
#     def get(self, request):
#         posts = Post.objects.all()
#         return render(request, 'posts/post_list.html', {'posts': posts})
#
def post_list_view(request):
    try:
        posts = Posts.objects.all()
        post_summary_list = []
        for post in posts:
             post_summary_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.content[:100]
        })
        return render(request = request, template_name ='post_list.html', context={'post_summary': post_summary_list})
    except Posts.DoesNotExist:
        return render(request, '404.html', status=404)

def post_detail_view(request, post_id):
    try:
        post = Posts.objects.get(id=post_id)
        return render(request = request, template_name = 'post_detail.html', context={'post': post})
    except Posts.DoesNotExist:
        return render(request, '404.html', status=404)
