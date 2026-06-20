"""Тесты форм приложения blog."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from blog.forms import CommentForm, PostForm, SignUpForm
from blog.tests.factories import create_category, create_location

User = get_user_model()


class CommentFormTest(TestCase):
    def test_valid_with_text(self):
        self.assertTrue(CommentForm(data={'text': 'Привет'}).is_valid())

    def test_invalid_without_text(self):
        self.assertFalse(CommentForm(data={'text': ''}).is_valid())


class PostFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = create_category()
        cls.location = create_location()

    def test_valid_data(self):
        form = PostForm(data={
            'title': 'Заголовок',
            'text': 'Текст',
            'pub_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'category': self.category.pk,
            'location': self.location.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_category_is_required(self):
        form = PostForm(data={
            'title': 'Заголовок',
            'text': 'Текст',
            'pub_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)


class SignUpFormTest(TestCase):
    def test_creates_user_with_email(self):
        form = SignUpForm(data={
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': 'Very-Strong-Pass-123',
            'password2': 'Very-Strong-Pass-123',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'newbie@example.com')
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_email_is_required(self):
        form = SignUpForm(data={
            'username': 'newbie',
            'password1': 'Very-Strong-Pass-123',
            'password2': 'Very-Strong-Pass-123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
