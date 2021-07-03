from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Group, Follow, Post, User
from yatube.settings import POSTS_PAGINATOR


def index(request):
    post_list = Post.objects.select_related('group').all()
    paginator = Paginator(post_list, POSTS_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'paginator': paginator}
    return render(request, 'index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'group': group, 'page': page, 'paginator': paginator}
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, POSTS_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = Follow.objects.filter(
        user=request.user.id,
        author=author.id
    )
    context = {
        'author': author,
        'page': page,
        'paginator': paginator,
        'following': following
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    form = CommentForm(instance=None)
    comments = post.comments.all()
    context = {
        'author': author,
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'post.html', context)


@login_required()
def new_post(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'new_post.html',
                      {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(reverse('posts:index'))


@login_required()
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('posts:post', args=[username, post_id])
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        context = {
            'post': post,
            'form': form
        }
        return render(request, 'new_post.html', context)
    form.save()
    return redirect(reverse(
        'posts:post',
        kwargs={'username': post.author.username, 'post_id': post.pk}
    ))


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect(
            'posts:post',
            post_id=post.pk,
            username=post.author.username
        )
    return render(
        request,
        'posts/include/comments.html',
        {'form': form, 'post': post}
    )


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user.
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, POSTS_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author == user:
        return redirect('posts:index')
    Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, author=author.id, user=request.user.id)
    follow.delete()
    return redirect('posts:profile', username=username)


def page_not_found(request, exception=None):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
