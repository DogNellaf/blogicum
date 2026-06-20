"""Тесты вьюх и бизнес-логики приложения blog."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Comment, Post
from blog.tests.factories import (
    create_category,
    create_comment,
    create_location,
    create_post,
    create_user,
)

User = get_user_model()


class BaseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = create_user('author')
        cls.reader = create_user('reader')
        cls.category = create_category()
        cls.unpub_category = create_category(
            slug='hidden', is_published=False, title='Скрытая'
        )
        cls.location = create_location()
        cls.post = create_post(
            cls.author, cls.category, location=cls.location, title='Опубл.'
        )

    def setUp(self):
        self.author_client = self.client_class()
        self.author_client.force_login(self.author)
        self.reader_client = self.client_class()
        self.reader_client.force_login(self.reader)


class PublicPagesTest(BaseViewTest):
    def test_index_available(self):
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/index.html')

    def test_category_page_available(self):
        url = reverse('blog:category_posts', args=[self.category.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/category.html')

    def test_unpublished_category_returns_404(self):
        url = reverse('blog:category_posts', args=[self.unpub_category.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_profile_page_available(self):
        url = reverse('blog:profile', args=[self.author.username])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/profile.html')

    def test_post_detail_available(self):
        url = reverse('blog:post_detail', args=[self.post.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/detail.html')


class ContentVisibilityTest(BaseViewTest):
    def test_index_hides_unpublished_future_and_hidden_category(self):
        draft = create_post(
            self.author, self.category, is_published=False, title='Черновик'
        )
        future = create_post(
            self.author, self.category, days_offset=5, title='Будущее'
        )
        hidden = create_post(
            self.author, self.unpub_category, title='Скрытая категория'
        )
        page_obj = self.client.get(reverse('blog:index')).context['page_obj']
        posts = list(page_obj)
        self.assertIn(self.post, posts)
        for hidden_post in (draft, future, hidden):
            self.assertNotIn(hidden_post, posts)

    def test_author_sees_own_unpublished_on_profile(self):
        draft = create_post(
            self.author, self.category, is_published=False, title='Черновик'
        )
        url = reverse('blog:profile', args=[self.author.username])
        posts = list(self.author_client.get(url).context['page_obj'])
        self.assertIn(draft, posts)

    def test_other_user_does_not_see_unpublished_on_profile(self):
        draft = create_post(
            self.author, self.category, is_published=False, title='Черновик'
        )
        url = reverse('blog:profile', args=[self.author.username])
        posts = list(self.reader_client.get(url).context['page_obj'])
        self.assertNotIn(draft, posts)

    def test_anonymous_cannot_open_unpublished_post(self):
        draft = create_post(
            self.author, self.category, is_published=False, title='Черновик'
        )
        url = reverse('blog:post_detail', args=[draft.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_can_open_own_unpublished_post(self):
        draft = create_post(
            self.author, self.category, is_published=False, title='Черновик'
        )
        url = reverse('blog:post_detail', args=[draft.pk])
        response = self.author_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_count_displayed_on_index(self):
        create_comment(self.post, self.reader)
        create_comment(self.post, self.author)
        page_obj = self.client.get(reverse('blog:index')).context['page_obj']
        post = next(p for p in page_obj if p.pk == self.post.pk)
        self.assertEqual(post.comments_count, 2)

    def test_comment_count_displayed_on_category(self):
        create_comment(self.post, self.reader)
        url = reverse('blog:category_posts', args=[self.category.slug])
        page_obj = self.client.get(url).context['page_obj']
        post = next(p for p in page_obj if p.pk == self.post.pk)
        self.assertEqual(post.comments_count, 1)


class PostCrudTest(BaseViewTest):
    def test_anonymous_create_redirects_to_login(self):
        response = self.client.get(reverse('blog:create_post'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse('login'), response.url)

    def test_authorized_user_creates_post(self):
        data = {
            'title': 'Новый пост',
            'text': 'Содержимое',
            'pub_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'category': self.category.pk,
            'location': self.location.pk,
        }
        response = self.reader_client.post(
            reverse('blog:create_post'), data
        )
        self.assertRedirects(
            response, reverse('blog:profile', args=[self.reader.username])
        )
        created = Post.objects.get(title='Новый пост')
        self.assertEqual(created.author, self.reader)

    def test_author_can_edit_own_post(self):
        url = reverse('blog:edit_post', args=[self.post.pk])
        data = {
            'title': 'Изменённый',
            'text': self.post.text,
            'pub_date': self.post.pub_date.strftime('%Y-%m-%dT%H:%M'),
            'category': self.category.pk,
        }
        response = self.author_client.post(url, data)
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk])
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Изменённый')

    def test_non_author_cannot_edit_post(self):
        url = reverse('blog:edit_post', args=[self.post.pk])
        data = {
            'title': 'Взлом',
            'text': 'x',
            'pub_date': self.post.pub_date.strftime('%Y-%m-%dT%H:%M'),
            'category': self.category.pk,
        }
        response = self.reader_client.post(url, data)
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk])
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Опубл.')

    def test_author_can_delete_post(self):
        post = create_post(self.author, self.category, title='Удаляемый')
        url = reverse('blog:delete_post', args=[post.pk])
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('blog:index'))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_non_author_cannot_delete_post(self):
        url = reverse('blog:delete_post', args=[self.post.pk])
        self.reader_client.post(url)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_confirmation_page_is_shown_on_get(self):
        url = reverse('blog:delete_post', args=[self.post.pk])
        response = self.author_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/create.html')


class CommentCrudTest(BaseViewTest):
    def test_anonymous_cannot_add_comment(self):
        url = reverse('blog:add_comment', args=[self.post.pk])
        response = self.client.post(url, {'text': 'Аноним'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authorized_user_adds_comment(self):
        url = reverse('blog:add_comment', args=[self.post.pk])
        response = self.reader_client.post(url, {'text': 'Хороший пост'})
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk])
        )
        comment = Comment.objects.get()
        self.assertEqual(comment.text, 'Хороший пост')
        self.assertEqual(comment.author, self.reader)
        self.assertEqual(comment.post, self.post)

    def test_add_comment_to_missing_post_returns_404(self):
        url = reverse('blog:add_comment', args=[999])
        response = self.reader_client.post(url, {'text': 'x'})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_can_edit_own_comment(self):
        comment = create_comment(self.post, self.reader, text='старый')
        url = reverse(
            'blog:edit_comment', args=[self.post.pk, comment.pk]
        )
        response = self.reader_client.post(url, {'text': 'новый'})
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk])
        )
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'новый')

    def test_non_author_cannot_edit_comment(self):
        comment = create_comment(self.post, self.reader, text='старый')
        url = reverse(
            'blog:edit_comment', args=[self.post.pk, comment.pk]
        )
        response = self.author_client.post(url, {'text': 'взлом'})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comment.refresh_from_db()
        self.assertEqual(comment.text, 'старый')

    def test_author_can_delete_own_comment(self):
        comment = create_comment(self.post, self.reader)
        url = reverse(
            'blog:delete_comment', args=[self.post.pk, comment.pk]
        )
        response = self.reader_client.post(url)
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk])
        )
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_non_author_cannot_delete_comment(self):
        comment = create_comment(self.post, self.reader)
        url = reverse(
            'blog:delete_comment', args=[self.post.pk, comment.pk]
        )
        self.author_client.post(url)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())


class FormPagesGetTest(BaseViewTest):
    """GET-запросы должны отдавать страницы с формами."""

    def test_create_post_form(self):
        response = self.author_client.get(reverse('blog:create_post'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/create.html')
        self.assertIn('form', response.context)

    def test_edit_post_form(self):
        url = reverse('blog:edit_post', args=[self.post.pk])
        response = self.author_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/create.html')

    def test_registration_form(self):
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(
            response, 'registration/registration_form.html'
        )

    def test_edit_profile_form(self):
        response = self.author_client.get(reverse('blog:edit_profile'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/user.html')

    def test_edit_comment_form(self):
        comment = create_comment(self.post, self.reader)
        url = reverse('blog:edit_comment', args=[self.post.pk, comment.pk])
        response = self.reader_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/comment.html')

    def test_delete_comment_confirmation(self):
        comment = create_comment(self.post, self.reader)
        url = reverse('blog:delete_comment', args=[self.post.pk, comment.pk])
        response = self.reader_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'blog/comment.html')


class ProfileAndAuthTest(BaseViewTest):
    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(reverse('registration'), {
            'username': 'fresh',
            'email': 'fresh@example.com',
            'password1': 'Very-Strong-Pass-123',
            'password2': 'Very-Strong-Pass-123',
        })
        self.assertRedirects(
            response, reverse('blog:profile', args=['fresh'])
        )
        self.assertTrue(User.objects.filter(username='fresh').exists())

    def test_user_can_edit_own_profile(self):
        response = self.author_client.post(reverse('blog:edit_profile'), {
            'username': self.author.username,
            'first_name': 'Иван',
            'last_name': 'Петров',
            'email': 'ivan@example.com',
        })
        self.assertRedirects(
            response, reverse('blog:profile', args=[self.author.username])
        )
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, 'Иван')

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse('blog:edit_profile'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse('login'), response.url)
