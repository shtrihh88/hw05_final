from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Начинаем тестировать проект!',
            author=User.objects.create(),
        )
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
        )

    def test_str_post(self):
        post = PostModelTests.post
        expected_str = post.text[:15]
        self.assertEqual(expected_str, str(post))

    def test_str_group(self):
        group = PostModelTests.group
        expected_str = group.title
        self.assertEqual(expected_str, str(group))
