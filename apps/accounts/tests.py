from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationViewTests(APITestCase):
    def test_registers_user(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "harry",
                "email": "harry@example.com",
                "password": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "harry")
        self.assertFalse("password" in response.data)
        self.assertTrue(get_user_model().objects.filter(username="harry").exists())

    def test_rejects_duplicate_username(self):
        get_user_model().objects.create_user(
            username="harry",
            email="other@example.com",
            password="StrongPassword123",
        )

        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "harry",
                "email": "harry2@example.com",
                "password": "StrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
