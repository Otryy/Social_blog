from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginator(request, post_list):
    post = Paginator(post_list, settings.AMOUNT_POSTS)
    page_number = request.GET.get('page')
    return post.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group')
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_count = author.posts.count()
    post_list = author.posts.select_related('author')
    page_obj = paginator(request, post_list)
    is_following = Follow.objects.filter(
        user=request.user.pk,
        author=author,
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_amount': posts_count,
        'is_following': is_following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    if request.method != 'POST':
        return render(request, 'posts/post_create.html', {
            'form': form,
            'post': post
        })

    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})

    form.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/post_detail.html', {'form': form})

    form.instance.author = request.user
    form.instance.post = post
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_show = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, posts_show)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(user=request.user.id, author=author)
    if request.user != author and not is_following.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_following = Follow.objects.filter(user=request.user.id, author=author)
    if is_following.exists():
        is_following.delete()
    return redirect('posts:profile', username=username)
