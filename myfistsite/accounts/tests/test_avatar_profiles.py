import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile


TEST_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
    b"\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class AvatarProfileTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_media_root = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media_root)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._temp_media_root, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPass123",
        )
        self.staff_user = user_model.objects.create_user(
            username="staff_user",
            email="staff@example.com",
            password="StrongPass123",
            is_staff=True,
        )
        Profile.objects.get_or_create(user=self.owner)
        Profile.objects.get_or_create(user=self.other_user)
        Profile.objects.get_or_create(user=self.staff_user)

    def _uploaded_avatar(self, name: str = "avatar.gif") -> SimpleUploadedFile:
        return SimpleUploadedFile(name, TEST_GIF, content_type="image/gif")

    def test_about_me_page_is_available_for_anonymous_user(self):
        response = self.client.get(reverse("accounts:about_me"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обо мне")
        self.assertContains(response, "нужно войти в аккаунт")

    def test_about_me_page_is_available_for_authenticated_user(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("accounts:about_me"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обо мне")
        self.assertContains(response, self.owner.username)

    def test_users_list_page_is_available(self):
        response = self.client.get(reverse("accounts:users_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner.username)
        self.assertContains(response, self.other_user.username)

    def test_user_detail_contains_edit_link_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("accounts:user_detail", kwargs={"pk": self.owner.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("accounts:user_profile_update", kwargs={"user_pk": self.owner.pk}),
        )

    def test_user_detail_does_not_contain_edit_link_without_permissions(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("accounts:user_detail", kwargs={"pk": self.other_user.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("accounts:user_profile_update", kwargs={"user_pk": self.other_user.pk}),
        )

    def test_owner_can_update_own_avatar_on_about_me_page(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("accounts:about_me"),
            {
                "avatar": self._uploaded_avatar(),
            },
        )

        self.assertRedirects(response, reverse("accounts:about_me"))
        profile = Profile.objects.get(user=self.owner)
        self.assertTrue(profile.avatar.name)
        self.assertTrue(Path(profile.avatar.path).exists())
        self.assertTrue(str(profile.avatar.path).startswith(self._temp_media_root))

    def test_owner_can_update_own_profile_without_avatar_field(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "full_name": "Owner Name",
                "email": "owner@example.com",
                "phone": "+70000000000",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        profile = Profile.objects.get(user=self.owner)
        self.assertEqual(profile.full_name, "Owner Name")
        self.assertEqual(profile.phone, "+70000000000")

    def test_staff_can_update_other_user_profile(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("accounts:user_profile_update", kwargs={"user_pk": self.other_user.pk}),
            {
                "full_name": "Updated By Staff",
                "email": "other@example.com",
                "phone": "+79999999999",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:user_detail", kwargs={"pk": self.other_user.pk}),
        )
        profile = Profile.objects.get(user=self.other_user)
        self.assertEqual(profile.full_name, "Updated By Staff")

    def test_non_staff_cannot_update_other_user_profile(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("accounts:user_profile_update", kwargs={"user_pk": self.other_user.pk})
        )

        self.assertEqual(response.status_code, 403)