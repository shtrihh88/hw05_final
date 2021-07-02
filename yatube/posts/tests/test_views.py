from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

import shutil
import tempfile

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_desc'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_post',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_fields_new_post = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('posts:index'),
            'group.html': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            'new_post.html': reverse('posts:new_post')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('page').object_list[0],
                         self.post)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        ))
        self.assertEqual(response.context['group'], self.group)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        for value, expected in self.form_fields_new_post.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_shows_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:edit',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.id
            }
        ))
        self.assertEqual(response.context['post'], self.post)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(response.context['author'], self.user)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post',
            kwargs={
                'username': self.user.username,
                'post_id': self.post.id
            }
        ))
        self.assertEqual(response.context['author'], self.user)

    def test_post_exists_on_main_page(self):
        """Тест на появление поста на главной страницы после создания"""
        # Запрос до создания поста
        response = self.authorized_client.get(reverse('posts:index'))
        count_posts_before = len(response.context['page'])
        # Создаем новую запись в бд
        post_created = Post.objects.create(
            text='new_post_test_text',
            author=self.user,
            group=self.group
        )
        # Запрос после создания поста
        response = self.authorized_client.get(reverse('posts:index'))
        count_posts_after = len(response.context['page'])
        new_post = response.context['page'].object_list[0]
        self.assertEqual(count_posts_before + 1, count_posts_after)
        self.assertEqual(post_created, new_post)

    def test_post_exists_on_related_group_page(self):
        """Тест на появление поста на странице группы после создания"""
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        ))
        self.assertEqual(response.context['page'].object_list[0], self.post)

    def test_posts_have_another_group(self):
        """Тест на непринадлежность к другой группе"""
        another_group = Group.objects.create(
            title='another',
            slug='another_slug',
            description='another_desc'
        )
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': another_group.slug}
        ))
        another_posts = response.context['page']
        self.assertNotEqual(another_posts, self.post)

    def test_index_post_image_context_correct(self):
        """ Тестирование картинки в context поста на index.html """
        response = self.authorized_client.get(reverse('posts:index'))

        test_image = response.context['page'].object_list[0].image
        self.assertEqual(test_image, self.post.image, (
            ' Картинка поста на главной странице неверно отображается '
        ))

    def test_cache(self):
        """ Тестирование работы кэша"""
        response_before = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.create(text='test', author=self.user)
        response_after = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(id=post.id).delete()
        response_after_delete = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(response_after.content, response_after_delete.content)
        cache.clear()
        response_after_clear = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(
            response_after_clear.context['paginator'].count,
            response_before.context['paginator'].count)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_desc'
        )
        for i in range(13):
            Post.objects.create(
                text=f'{i} text',
                author=cls.user,
                group=cls.group
            )

    def test_index_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_index_second_page_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:index'
        ) + '?page=2')
        self.assertEqual(len(response.context['page'].object_list), 3)

    def test_first_page_in_group_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        ))
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_second_page_in_group_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        ) + '?page=2')
        self.assertEqual(len(response.context['page'].object_list), 3)

    def test_first_page_in_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_second_page_in_profile_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ) + '?page=2')
        self.assertEqual(len(response.context['page'].object_list), 3)


class TestComment(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.post = Post.objects.create(text='test_text', author=cls.user)

    def test_authorized_user_comments_posts(self):
        """Проверка на добавление комментария авторизованным юзером."""
        self.client.force_login(TestComment.user)

        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'username': TestComment.user.username,
                    'post_id': TestComment.post.id}),
                data={'text': 'Комментарий авторизированного пользователя'},
                follow=True)

        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий авторизированного пользователя',
                post_id=TestComment.post.id).exists())

    def test_comment_not_authorized(self):
        """Проверка на добавление комментария не авторизованным юзером."""
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'username': TestComment.user.username,
                    'post_id': TestComment.post.id}),
                data={'text': 'Комментарий неавторизированного пользователя'},
                follow=True)

        self.assertFalse(
            Comment.objects.filter(
                text='Комментарий неавторизированного пользователя',
                post_id=TestComment.post.id).exists())
