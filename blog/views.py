from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.forms import CommentForm, PostForm, ProfileForm, SignUpForm
from blog.models import Category, Comment, Post

User = get_user_model()


def paginate(request, queryset):
    """Вернуть страницу пагинатора для переданного queryset."""
    paginator = Paginator(queryset, settings.DEFAULT_POST_LIMIT)
    return paginator.get_page(request.GET.get('page'))


def index(request):
    posts = Post.objects.with_related().published().with_comment_count()
    return render(request, 'blog/index.html', {
        'page_obj': paginate(request, posts),
    })


def category_posts(request, category):
    category_obj = get_object_or_404(
        Category, slug=category, is_published=True
    )
    posts = (
        Post.objects.with_related()
        .published()
        .with_comment_count()
        .filter(category=category_obj)
    )
    return render(request, 'blog/category.html', {
        'category': category_obj,
        'page_obj': paginate(request, posts),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.with_related(), id=post_id)

    is_visible = (
        post.is_published
        and post.pub_date <= timezone.now()
        and post.category is not None
        and post.category.is_published
    )
    if post.author != request.user and not is_visible:
        raise Http404('Публикация не найдена.')

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.select_related('author'),
    })


def user_profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = (
        Post.objects.with_related()
        .with_comment_count()
        .filter(author=profile)
    )
    # Чужой профиль показывает только опубликованные посты.
    if request.user != profile:
        posts = posts.published()

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': paginate(request, posts),
    })


def registration(request):
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('blog:profile', username=user.username)
    return render(request, 'registration/registration_form.html',
                  {'form': form})


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html',
                  {'form': PostForm(instance=post)})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment, id=comment_id, post_id=post_id, author=request.user
    )
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment, id=comment_id, post_id=post_id, author=request.user
    )
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
