from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.core.models import Category

def organization_document_upload_to(instance, filename):
    return f"organizations/{instance.pk or 'new'}/{filename}"

def organization_request_document_upload_to(instance, filename):
    return f"organization-registration-requests/{instance.pk or 'new'}/{filename}"


def organization_common_document_upload_to(instance, filename):
    if instance._meta.model_name == "organizationregistrationrequest":
        return organization_request_document_upload_to(instance, filename)
    return organization_document_upload_to(instance, filename)

class OrganizationCommonFieldsMixin(models.Model):
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
        upload_to=organization_common_document_upload_to,
        verbose_name="Устав",
    )
    inn_certificate = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Свидетельство о присвоении ИНН",
    )
    state_registration_certificate = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО",
    )
    founders_appointment_decision = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа",
    )
    executive_passport_copy = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа",
    )
    egrul_extract = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Выписка из ЕГРЮЛ",
    )
    nko_registry_notice = models.FileField(
        upload_to=organization_common_document_upload_to,
        verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(OrganizationCommonFieldsMixin):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
        verbose_name="Создатель",
    )

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


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        allow_unicode=True,
        verbose_name="Slug",
    )
    content = models.TextField(verbose_name="Описание")
    image = models.ImageField(
        upload_to="events/",
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="events",
        limit_choices_to={"scope": Category.Scope.EVENT},
        verbose_name="Категория",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Организация",
    )
    created_by_member = models.ForeignKey(
        OrganizationMember,
        on_delete=models.PROTECT,
        related_name="created_events",
        verbose_name="Создатель",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус",
    )
    starts_at = models.DateTimeField(verbose_name="Дата начала")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата окончания")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    is_online = models.BooleanField(default=False, verbose_name="Онлайн")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Опубликовано")

    class Meta:
        db_table = "events"
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ("-starts_at", "-created_at")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.category_id and self.category.scope != Category.Scope.EVENT:
            raise ValidationError({"category": "Для мероприятия нужна категория мероприятий."})
        if (
            self.created_by_member_id
            and self.organization_id
            and self.created_by_member.organization_id != self.organization_id
        ):
            raise ValidationError(
                {"created_by_member": "Создатель должен быть участником этой организации."}
            )
        if self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({"ends_at": "Дата окончания не может быть раньше даты начала."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class OrganizationRegistrationRequest(OrganizationCommonFieldsMixin):
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_registration_requests",
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

    class Meta:
        db_table = "organization_registration_requests"
        verbose_name = "Заявка на регистрацию организации"
        verbose_name_plural = "Заявки на регистрацию организаций"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.official_name} ({self.status})"
