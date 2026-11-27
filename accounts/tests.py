import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import CustomUserCreationForm, UserProfileForm
from .models import CustomUser


class RegistrationAndProfileRoleTests(TestCase):
    def test_registration_does_not_offer_or_accept_a_role(self):
        registration_page = self.client.get(reverse('register'))
        self.assertNotContains(registration_page, 'Role')
        self.assertNotIn('role', CustomUserCreationForm.base_fields)

        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-player',
                'email': 'new-player@example.com',
                'first_name': 'New',
                'last_name': 'Player',
                'role': CustomUser.Role.COURT_ADMIN,
                'password1': 'Safe-password-482!',
                'password2': 'Safe-password-482!',
            },
        )

        self.assertRedirects(response, reverse('login'))
        user = CustomUser.objects.get(username='new-player')
        self.assertEqual(user.role, CustomUser.Role.PLAYER)

    def test_profile_pages_do_not_show_or_edit_role(self):
        user = CustomUser.objects.create_user(
            username='profile-role-user',
            password='test-password',
        )
        self.client.force_login(user)

        profile_response = self.client.get(reverse('profile'))
        edit_response = self.client.get(reverse('profile_edit'))

        self.assertNotContains(profile_response, 'Role')
        self.assertNotContains(edit_response, 'Role')
        self.assertNotContains(profile_response, 'City')
        self.assertNotContains(edit_response, 'City')
        self.assertNotIn('role', UserProfileForm.base_fields)
        self.assertNotIn('city', UserProfileForm.base_fields)

    def test_user_can_add_multiple_valid_social_links(self):
        user = CustomUser.objects.create_user(
            username='social-links-user',
            password='test-password',
        )
        self.client.force_login(user)
        social_links = [
            'https://instagram.com/picklescout-user',
            'https://facebook.com/picklescout-user',
        ]

        edit_response = self.client.get(reverse('profile_edit'))
        self.assertContains(edit_response, 'Add one full social profile URL per line.')

        response = self.client.post(
            reverse('profile_edit'),
            {'social_links': '\n'.join(social_links)},
        )

        self.assertRedirects(response, reverse('profile'))
        user.refresh_from_db()
        self.assertEqual(user.social_links, social_links)
        profile_response = self.client.get(reverse('profile'))
        for social_link in social_links:
            self.assertContains(profile_response, social_link)

    def test_social_links_reject_invalid_urls(self):
        user = CustomUser.objects.create_user(
            username='invalid-social-links-user',
            password='test-password',
        )
        form = UserProfileForm(
            data={'social_links': 'javascript:alert(1)'},
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('social_links', form.errors)


class AuthenticationRouteAccessTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='route-access-user',
            password='test-password',
        )

    def test_authenticated_users_are_redirected_from_login_and_signup(self):
        self.client.force_login(self.user)

        for route_name in ('login', 'register'):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(response, reverse('dashboard'))

    def test_anonymous_users_are_redirected_from_private_pages(self):
        private_routes = ('profile', 'profile_edit', 'dashboard', 'admin_panel')

        for route_name in private_routes:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url.split('?')[0], reverse('landing'))
                self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_regular_user_is_redirected_from_system_admin_panel(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('admin_panel'))

        self.assertRedirects(response, reverse('dashboard'))

    def test_logout_returns_user_to_landing_page(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('landing'))


class ProfilePhotoUploadTests(TestCase):
    def setUp(self):
        media_root = tempfile.TemporaryDirectory()
        self.addCleanup(media_root.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_root.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.user = CustomUser.objects.create_user(
            username='profile-photo-user',
            password='test-password',
        )
        self.client.force_login(self.user)

    def test_user_can_upload_and_see_profile_photo(self):
        edit_response = self.client.get(reverse('profile_edit'))
        self.assertContains(edit_response, 'Choose an image to use as your profile picture.')

        image_buffer = io.BytesIO()
        Image.new('RGB', (2, 2), color='green').save(image_buffer, format='PNG')
        image = SimpleUploadedFile(
            'avatar.png',
            image_buffer.getvalue(),
            content_type='image/png',
        )

        response = self.client.post(
            reverse('profile_edit'),
            {'profile_photo': image},
        )

        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_photo.name.startswith('profile_photos/'))

        profile_response = self.client.get(reverse('profile'))
        self.assertContains(profile_response, self.user.profile_photo.url)
