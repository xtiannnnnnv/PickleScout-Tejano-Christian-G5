import io
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import CustomUser


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
