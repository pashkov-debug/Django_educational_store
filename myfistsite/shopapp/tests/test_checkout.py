from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CheckoutStateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student",
            email="student@example.com",
            password="StrongPass123",
        )

    def test_checkout_city_cookie_set_and_read_supports_unicode(self):
        response = self.client.post(
            reverse("shopapp:checkout_city_set"),
            {"value": "Казань"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("checkout_city", self.client.cookies)

        read_response = self.client.get(reverse("shopapp:checkout_city_read"))

        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["value"], "Казань")

    def test_checkout_state_views_return_defaults_when_data_missing(self):
        city_response = self.client.get(reverse("shopapp:checkout_city_read"))
        address_response = self.client.get(reverse("shopapp:checkout_address_read"))

        self.assertEqual(city_response.json()["value"], "Город не выбран")
        self.assertEqual(address_response.json()["value"], "Адрес не заполнен")

    def test_checkout_address_session_set_and_read_supports_unicode(self):
        response = self.client.post(
            reverse("shopapp:checkout_address_set"),
            {"value": "Москва, ул. Пушкина, дом 1"},
        )

        self.assertEqual(response.status_code, 200)

        read_response = self.client.get(reverse("shopapp:checkout_address_read"))

        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["value"], "Москва, ул. Пушкина, дом 1")
