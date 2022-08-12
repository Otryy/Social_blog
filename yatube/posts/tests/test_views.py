import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='pag_auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([(Post(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост' + str(x)
        )) for x in range(1, 14)])

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.client.get(reverse('posts:index') + '?page=1')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            'posts/profile.html':
                reverse('posts:profile', kwargs={'username': f'{self.user}'}),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': f'{self.post.id}'})
            ),
            'posts/post_create.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(response.context['group'].title, 'Тестовый заголовок')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', kwargs={
                    'username': self.user.username}),
        )
        self.assertEqual(response.context['author'].username, 'auth')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                    'post_id': f'{self.post.id}'}),
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].author, self.post.author)
        self.assertEqual(response.context['post'].group, self.post.group)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}),
        )
        tested_fields = {
            response.context.get('form').initial['text']:
                PostPagesTests.post.text,
            response.context.get('form').initial['group']:
            PostPagesTests.post.group.id
        }
        for value, expected in tested_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_in_index(self):
        """Проверяем, что созаднный пост, есть на index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(self.post, first_object)

    def test_create_post_in_group(self):
        """Проверяем, что созаднный пост, есть на станице group"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group_list_obj = response.context['page_obj'][0]
        self.assertEqual(self.post, group_list_obj)

    def test_create_post_in_profile(self):
        """Проверяем, что созаднный пост, есть на profile"""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        post_detail_obj = response.context['page_obj'][0]
        self.assertEqual(self.post, post_detail_obj)


class CacheTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.client

    def test_cache(self):
        """Тест кэширования главной страницы"""
        first_request = self.client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Написано что-то интересное'
        post_1.save()
        second_request = self.client.get(reverse('posts:index'))
        self.assertEqual(first_request.content, second_request.content)
        cache.clear()
        third_request = self.client.get(reverse('posts:index'))
        self.assertNotEqual(first_request.content, third_request.content)


class FollowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = self.user
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовый текст'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.user_no_author = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow(self):
        """Пользователь может подписываться на других пользователей."""
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        follow_exist = Follow.objects.filter(user=self.user_follower,
                                             author=self.user_following
                                             ).exists()
        self.assertTrue(follow_exist)

    def test_unfollow(self):
        """Пользователь может отписываться от других пользователей."""
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        follow_exist = Follow.objects.filter(user=self.user_following,
                                             author=self.user_follower
                                             ).exists()
        self.assertFalse(follow_exist)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        self.assertIn('page_obj', response.context)
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, self.post.text)

    def test_subscription_feed_not_follow(self):
        """Запись не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user_following,
                              author=self.user_following)
        response = self.client_auth_following.get(
            reverse('posts:follow_index'))
        post_text = response.context["page_obj"][0].text
        self.assertIn('page_obj', response.context)
        self.assertEqual(post_text, self.post.text)

    def test_not_follow_user_user(self):
        """Пользователь не может пописаться сам на себя."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=self.user).exists()
        self.assertFalse(follow_exist)
