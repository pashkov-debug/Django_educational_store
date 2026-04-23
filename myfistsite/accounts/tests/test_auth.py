from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer_auth",
            email="buyer_auth@example.com",
            password="StrongPass123",
        )

    def test_login_page_redirects_authenticated_user_to_home(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:login"))

        self.assertRedirects(response, reverse("shopapp:index"))

    def test_login_with_valid_credentials_authenticates_user(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "buyer_auth",
                "password": "StrongPass123",
            },
        )

        self.assertRedirects(response, reverse("shopapp:index"))
        homepage_response = self.client.get(reverse("shopapp:index"))
        self.assertTrue(homepage_response.wsgi_request.user.is_authenticated)
        self.assertEqual(homepage_response.wsgi_request.user.username, "buyer_auth")

    def test_login_with_invalid_credentials_does_not_authenticate_user(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "buyer_auth",
                "password": "WrongPassword123",
            },
        )

        self.assertEqual(response.status_code, 200)
        homepage_response = self.client.get(reverse("shopapp:index"))
        self.assertFalse(homepage_response.wsgi_request.user.is_authenticated)

    def test_register_page_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newbuyer",
                "email": "newbuyer@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        self.assertRedirects(response, reverse("shopapp:index"))
        created_user = get_user_model().objects.get(username="newbuyer")
        self.assertEqual(created_user.email, "newbuyer@example.com")

        homepage_response = self.client.get(reverse("shopapp:index"))
        self.assertTrue(homepage_response.wsgi_request.user.is_authenticated)

    def test_logout_view_logs_out_user_and_redirects_home(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("shopapp:index"))
        homepage_response = self.client.get(reverse("shopapp:index"))
        self.assertFalse(homepage_response.wsgi_request.user.is_authenticated)

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "brokenbuyer",
                "email": "brokenbuyer@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass99999",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="brokenbuyer").exists()
        )

    def test_register_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "buyer_auth",
                "email": "another@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            get_user_model().objects.filter(username="buyer_auth").count(),
            1,
        )

    def test_register_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newusername",
                "email": "buyer_auth@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="newusername").exists()
        )
