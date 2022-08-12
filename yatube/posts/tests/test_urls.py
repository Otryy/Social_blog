from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TemplateURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        cache.clear()

    def test_urls_for_authorized_exists(self):
        """Страница доступна авторизованным пользователям."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_for_author_exists(self):
        """Cтраница редактирования поста доступна только автору поста"""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соотвествующие шаблоны"""
        template_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
        }
        for address, template in template_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('/n0t_ex15ting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_comment_authorized(self):
        """Комментировать может только авторизованный пользователь"""
        response = self.guest_client.get(reverse('posts:add_comment',
                                              kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
