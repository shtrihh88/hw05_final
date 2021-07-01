from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Test_User')
        cls.autorized_client = Client()
        cls.autorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_text',
            author=cls.user,
            group=cls.group
        )

    def test_create_post(self):
        """Тест на создание поста и редирект на главную страницу"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test_post_from_form',
            'group': self.group.id
        }
        response = self.autorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.group.id,
            author=self.user
        ).exists())
        last_post = Post.objects.filter().order_by('-id')[0]
        self.assertEqual(form_data['text'], last_post.text)
        self.assertRedirects(response, reverse('posts:index'))

    def test_edit_post(self):
        """Тест на редактирование поста"""
        new_text = 'new_text'
        form_data = {
            'text': new_text,
            'group': self.group.id
        }
        self.autorized_client.post(
            reverse(
                'posts:edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            data=form_data
        )
        response = self.autorized_client.get(
            reverse(
                'posts:post',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            )
        )
        self.assertEqual(response.context['post'].text, new_text)
        self.assertTrue(Post.objects.filter(
            text=new_text,
            group=self.group.id
        ).exists())
