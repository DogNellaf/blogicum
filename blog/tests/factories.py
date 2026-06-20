"""Хелперы для создания тестовых данных."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from blog.models import Category, Comment, Location, Post

User = get_user_model()


def create_user(username='author', **kwargs):
    return User.objects.create_user(
        username=username,
        password='Very-Strong-Pass-123',
        **kwargs,
    )


def create_category(slug='news', is_published=True, **kwargs):
    return Category.objects.create(
        title=kwargs.pop('title', 'Новости'),
        slug=slug,
        is_published=is_published,
        **kwargs,
    )


def create_location(name='Москва', is_published=True):
    return Location.objects.create(name=name, is_published=is_published)


def create_post(author, category, *, is_published=True, days_offset=-1,
                location=None, title='Пост', text='Текст поста'):
    """Создать публикацию. days_offset<0 — прошлое, >0 — будущее."""
    return Post.objects.create(
        title=title,
        text=text,
        author=author,
        category=category,
        location=location,
        is_published=is_published,
        pub_date=timezone.now() + timedelta(days=days_offset),
    )


def create_comment(post, author, text='Комментарий'):
    return Comment.objects.create(post=post, author=author, text=text)
