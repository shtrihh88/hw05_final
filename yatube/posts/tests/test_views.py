from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post

User = get_user_model()


class PostPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_desc'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_post',
            group=cls.group
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
        self.assertEqual(response.context.get('page').object_list[-1],
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
