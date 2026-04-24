from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegistrationFlowTests(APITestCase):
    register_url = "/api/v1/accounts/register/"
    login_url = "/api/v1/accounts/login/"

    def test_registration_sends_verification_email_and_keeps_user_inactive(self):
        response = self.client.post(
            self.register_url,
            {
                "username": "harry",
                "email": "harry@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "first_name": "Harry",
                "last_name": "Potter",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Please verify your email", response.data["message"])

        user = get_user_model().objects.get(email="harry@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/api/v1/accounts/verify-email/", mail.outbox[0].body)

    def test_login_requires_verified_email(self):
        user = get_user_model().objects.create_user(
            username="harry",
            email="harry@example.com",
            password="StrongPassword123!",
            is_active=False,
            is_email_verified=False,
        )

        response = self.client.post(
            self.login_url,
            {
                "email": user.email,
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email address is not verified.", str(response.data))

    def test_email_verification_activates_user_and_allows_login(self):
        user = get_user_model().objects.create_user(
            username="harry",
            email="harry@example.com",
            password="StrongPassword123!",
            is_active=False,
            is_email_verified=False,
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = reverse("verify_email", kwargs={"uidb64": uidb64, "token": token})

        verify_response = self.client.get(verify_url, format="json")
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

        login_response = self.client.post(
            self.login_url,
            {
                "email": user.email,
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
