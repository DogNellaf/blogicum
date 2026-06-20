"""Тесты моделей и менеджера Post."""
from django.test import TestCase

from blog.models import STR_DISPLAY_LENGTH, Post
from blog.tests.factories import (
    create_category,
    create_comment,
    create_location,
    create_post,
    create_user,
)


class ModelStrTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = create_user()
        cls.category = create_category()
        cls.location = create_location()
        cls.post = create_post(cls.author, cls.category, location=cls.location)

    def test_category_str(self):
        self.assertEqual(str(self.category), self.category.title)

    def test_location_str(self):
        self.assertEqual(str(self.location), self.location.name)

    def test_post_str(self):
        self.assertEqual(str(self.post), self.post.title)

    def test_comment_str_is_truncated(self):
        long_text = 'я' * 100
        comment = create_comment(self.post, self.author, text=long_text)
        self.assertEqual(str(comment), long_text[:STR_DISPLAY_LENGTH])
        self.assertLessEqual(len(str(comment)), STR_DISPLAY_LENGTH)

    def test_post_get_absolute_url(self):
        self.assertEqual(
            self.post.get_absolute_url(), f'/posts/{self.post.pk}/'
        )

    def test_comment_get_absolute_url(self):
        comment = create_comment(self.post, self.author)
        self.assertEqual(
            comment.get_absolute_url(), f'/posts/{self.post.pk}/'
        )


class PostQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = create_user()
        cls.category = create_category()
        cls.unpub_category = create_category(
            slug='hidden', is_published=False, title='Скрытая'
        )
        cls.published = create_post(cls.author, cls.category, title='Опубл.')
        cls.draft = create_post(
            cls.author, cls.category, is_published=False, title='Черновик'
        )
        cls.future = create_post(
            cls.author, cls.category, days_offset=5, title='Будущее'
        )
        cls.hidden_cat = create_post(
            cls.author, cls.unpub_category, title='Скрытая категория'
        )

    def test_published_returns_only_visible_posts(self):
        published = list(Post.objects.published())
        self.assertIn(self.published, published)
        self.assertNotIn(self.draft, published)
        self.assertNotIn(self.future, published)
        self.assertNotIn(self.hidden_cat, published)

    def test_default_manager_returns_everything(self):
        self.assertEqual(Post.objects.count(), 4)

    def test_with_comment_count_annotation(self):
        create_comment(self.published, self.author)
        create_comment(self.published, self.author)
        post = (
            Post.objects.with_comment_count()
            .get(pk=self.published.pk)
        )
        self.assertEqual(post.comments_count, 2)

    def test_with_comment_count_ordering_is_newest_first(self):
        posts = list(Post.objects.with_comment_count())
        pub_dates = [post.pub_date for post in posts]
        self.assertEqual(pub_dates, sorted(pub_dates, reverse=True))
