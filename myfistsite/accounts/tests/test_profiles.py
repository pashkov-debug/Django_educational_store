from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile


class AccountsProfileTests(TestCase):
    def test_register_creates_profile_for_new_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "profilebuyer",
                "email": "profilebuyer@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        self.assertRedirects(response, reverse("shopapp:index"))

        user = get_user_model().objects.get(username="profilebuyer")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_is_linked_to_created_user_correctly(self):
        self.client.post(
            reverse("accounts:register"),
            {
                "username": "linkedbuyer",
                "email": "linkedbuyer@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        user = get_user_model().objects.get(username="linkedbuyer")
        profile = Profile.objects.get(user=user)

        self.assertEqual(profile.user, user)
        self.assertEqual(profile.user.username, "linkedbuyer")
