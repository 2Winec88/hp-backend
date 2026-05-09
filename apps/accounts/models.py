from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.common.file_validators import image_file_validators

import secrets


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        validators=image_file_validators,
    )
    bio = models.TextField(max_length=500, blank=True)
    is_email_verified = models.BooleanField(default=False)
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class CourierProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="courier_profile",
    )
    car_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "collections_courierprofile"
        verbose_name = "Courier profile"
        verbose_name_plural = "Courier profiles"
        ordering = ("user__email", "id")

    def __str__(self):
        return f"{self.user} - {self.car_name}"


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_codes",
    )
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_verification_codes"
        verbose_name = "Email verification code"
        verbose_name_plural = "Email verification codes"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} ({self.code})"

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def generate_code(cls):
        return f"{secrets.randbelow(1_000_000):06d}"
