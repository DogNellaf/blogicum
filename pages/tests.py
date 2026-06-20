"""Тесты статичных страниц и кастомных обработчиков ошибок."""
from http import HTTPStatus

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from pages.views import csrf_failure, server_error


class StaticPagesTest(TestCase):
    def test_about_page(self):
        response = self.client.get(reverse('pages:about'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'pages/about.html')

    def test_rules_page(self):
        response = self.client.get(reverse('pages:rules'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'pages/rules.html')


@override_settings(DEBUG=False)
class ErrorHandlersTest(TestCase):
    def test_custom_404(self):
        response = self.client.get('/this-page-does-not-exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'pages/404.html')

    def test_custom_500(self):
        request = RequestFactory().get('/')
        response = server_error(request)
        self.assertEqual(
            response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR
        )

    def test_custom_403_csrf(self):
        request = RequestFactory().get('/')
        response = csrf_failure(request, reason='test')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
