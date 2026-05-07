from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.models import City, GeoData

from .models import EmailVerificationCode


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class RegistrationFlowTests(APITestCase):
    register_url = "/api/v1/accounts/register/"
    verify_url = "/api/v1/accounts/verify-email/"
    login_url = "/api/v1/accounts/login/"

    def test_registration_sends_verification_email_and_keeps_user_inactive(self):
        with self.captureOnCommitCallbacks(execute=True):
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
        verification_code = EmailVerificationCode.objects.get(user=user)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(verification_code.code, mail.outbox[0].body)

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
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        verify_response = self.client.post(
            self.verify_url,
            {
                "email": user.email,
                "code": verification_code.code,
            },
            format="json",
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        verification_code.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertIsNotNone(verification_code.used_at)

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


class ProfileGeoDataTests(APITestCase):
    profile_url = "/api/v1/accounts/profile/"

    def test_user_can_store_geodata_reference(self):
        user = get_user_model().objects.create_user(
            username="geo-profile",
            email="geo-profile@example.com",
            password="StrongPassword123!",
            is_active=True,
            is_email_verified=True,
        )
        city, _ = City.objects.get_or_create(
            geoname_id=1486209,
            defaults={"name": "Yekaterinburg"},
        )
        geodata = GeoData.objects.create(
            city=city,
            street="Lenina, 1",
            latitude="56.838011",
            longitude="60.597465",
        )
        self.client.force_authenticate(user)

        response = self.client.patch(
            self.profile_url,
            data={"geodata": geodata.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.geodata, geodata)
