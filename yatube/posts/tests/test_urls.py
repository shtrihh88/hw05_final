from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_desc'
        )
        cls.author = User.objects.create_user(username='test_user')
        cls.no_author = User.objects.create_user(username='no_author_user')
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_post'
        )
        cls.templates_url_names = {
            'index.html': reverse('posts:index'),
            'group.html': reverse(
                'posts:group_posts',
                kwargs={'slug': cls.group.slug}
            ),
            'new_post.html': reverse('posts:new_post'),
            'profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.author.username}
            ),
            'post.html': reverse(
                'posts:post',
                kwargs={
                    'username': cls.author.username,
                    'post_id': cls.post.id
                }
            )
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

    def test_url_for_guest_user(self):
        """
        Доступность URL гостевому пользователю и проверка редиректа
        недоступных страниц.
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse('posts:new_post'):
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(reverse(
            'posts:edit',
            kwargs={
                'username': self.author.username,
                'post_id': self.post.id
            }
        ))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_for_authorized_user(self):
        """Доступность URL авторизованному пользователю автору поста."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_no_author_user(self):
        """
        Доступность URL авторизованному пользователю НЕ автору поста.
        """
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == reverse(
                        'posts:edit',
                        kwargs={
                            'username': self.author.username,
                            'post_id': self.post.id
                        }
                ):
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_not_found(self):
        """Сервер возвращает код 404"""
        response = self.guest_client.get('/not_page_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
