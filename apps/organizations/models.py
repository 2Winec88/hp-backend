from django.conf import settings
from django.db import models


def organization_document_upload_to(instance, filename):
    return f"organizations/{instance.pk or 'new'}/{filename}"


def organization_request_document_upload_to(instance, filename):
    return f"organization-registration-requests/{instance.pk or 'new'}/{filename}"


class Organization(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
        verbose_name="Создатель",
    )

    # Основная информация
    official_name = models.CharField(
        max_length=255,
        verbose_name="Официальное название организации",
    )
    legal_address = models.CharField(
        max_length=500,
        verbose_name="Юридический адрес",
    )
    phone = models.CharField(
        max_length=50,
        verbose_name="Телефон",
    )
    email = models.EmailField(
        verbose_name="Email",
    )

    # Исполнительный орган
    executive_person_full_name = models.CharField(
        max_length=255,
        verbose_name="ФИО исполнительного лица",
    )
    executive_authority_basis = models.CharField(
        max_length=500,
        verbose_name="Действующий на основании",
    )
    executive_body_name = models.CharField(
        max_length=255,
        verbose_name="Наименование исполнительного органа",
    )

    # Документы
    charter_document = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Устав",
    )
    inn_certificate = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Свидетельство о присвоении ИНН",
    )
    state_registration_certificate = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО",
    )
    founders_appointment_decision = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа",
    )
    executive_passport_copy = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа",
    )
    egrul_extract = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Выписка из ЕГРЮЛ",
    )
    nko_registry_notice = models.FileField(
        upload_to=organization_document_upload_to,
        verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        ordering = ("official_name",)

    def __str__(self):
        return self.official_name


class OrganizationMember(models.Model):
    class Role(models.TextChoices):
        MANAGER = "manager", "Менеджер"
        MEMBER = "member", "Участник"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_members"
        verbose_name = "Участник организации"
        verbose_name_plural = "Участники организаций"
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "user"),
                name="unique_organization_member",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.organization} ({self.role})"


class OrganizationRegistrationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_registration_requests",
    )

    # Основная информация
    official_name = models.CharField(
        max_length=255,
        verbose_name="Официальное название организации",
    )
    legal_address = models.CharField(max_length=500, verbose_name="Юридический адрес")
    phone = models.CharField(max_length=50, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")

    # Исполнительный орган
    executive_person_full_name = models.CharField(
        max_length=255,
        verbose_name="ФИО исполнительного лица",
    )
    executive_authority_basis = models.CharField(
        max_length=500,
        verbose_name="Действующий на основании",
    )
    executive_body_name = models.CharField(
        max_length=255,
        verbose_name="Наименование исполнительного органа",
    )

    # Документы
    charter_document = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Устав",
    )
    inn_certificate = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Свидетельство о присвоении ИНН",
    )
    state_registration_certificate = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО",
    )
    founders_appointment_decision = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа",
    )
    executive_passport_copy = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа",
    )
    egrul_extract = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Выписка из ЕГРЮЛ",
    )
    nko_registry_notice = models.FileField(
        upload_to=organization_request_document_upload_to,
        verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_organization_registration_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_request",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_registration_requests"
        verbose_name = "Заявка на регистрацию организации"
        verbose_name_plural = "Заявки на регистрацию организаций"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.official_name} ({self.status})"
