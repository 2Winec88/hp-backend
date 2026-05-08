from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

def organization_document_upload_to(instance, filename):
    return f"organizations/{instance.pk or 'new'}/{filename}"

def organization_request_document_upload_to(instance, filename):
    return f"organization-registration-requests/{instance.pk or 'new'}/{filename}"


def event_image_upload_to(instance, filename):
    return f"events/{instance.event_id or 'new'}/images/{filename}"


def organization_news_image_upload_to(instance, filename):
    return f"organizations/{instance.organization_id or 'new'}/news/{filename}"


def organization_news_gallery_image_upload_to(instance, filename):
    return f"organizations/{instance.news.organization_id or 'new'}/news/{instance.news_id or 'new'}/images/{filename}"


def organization_branch_image_upload_to(instance, filename):
    return f"organizations/{instance.branch.organization_id or 'new'}/branches/{instance.branch_id or 'new'}/images/{filename}"


def event_news_image_upload_to(instance, filename):
    return f"events/{getattr(instance, 'event_id', None) or 'new'}/news/{filename}"


def organization_common_document_upload_to(instance, filename):
    if instance._meta.model_name == "organizationregistrationrequest":
        return organization_request_document_upload_to(instance, filename)
    return organization_document_upload_to(instance, filename)


class Category(models.Model):
    """Модель категории для Мероприятий"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(
        max_length=100,
        blank=True,
        allow_unicode=True,
        verbose_name="Slug",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        db_table = "categories"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Organization(models.Model):
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
    max_url = models.URLField(blank=True, verbose_name="MAX")
    vk_url = models.URLField(blank=True, verbose_name="VK")
    website_url = models.URLField(blank=True, verbose_name="Website")

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
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
        verbose_name="Создатель",
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
    is_active = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="removed_organization_memberships",
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


class OrganizationBranch(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="branches",
        verbose_name="Organization",
    )
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_branches",
    )
    name = models.CharField(max_length=200, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone")
    email = models.EmailField(blank=True, verbose_name="Email")
    working_hours = models.TextField(blank=True, verbose_name="Working hours")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated")

    class Meta:
        db_table = "organization_branches"
        verbose_name = "Organization branch"
        verbose_name_plural = "Organization branches"
        ordering = ("organization__official_name", "name", "id")

    def __str__(self):
        return f"{self.name} ({self.organization})"


class OrganizationBranchImage(models.Model):
    branch = models.ForeignKey(
        OrganizationBranch,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Branch",
    )
    image = models.ImageField(
        upload_to=organization_branch_image_upload_to,
        verbose_name="Image",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Alternative text",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Sort order",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")

    class Meta:
        db_table = "organization_branch_images"
        verbose_name = "Organization branch image"
        verbose_name_plural = "Organization branch images"
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.branch} - {self.image.name}"


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
        verbose_name="Категория",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Организация",
    )
    geodata = models.ForeignKey(
        "common.GeoData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    
    created_by_member = models.ForeignKey(
        OrganizationMember,
        on_delete=models.CASCADE,
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
    max_url = models.URLField(blank=True, verbose_name="MAX post")
    vk_url = models.URLField(blank=True, verbose_name="VK post")
    website_url = models.URLField(blank=True, verbose_name="Website event page")
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


class EventImage(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Мероприятие",
    )
    image = models.ImageField(
        upload_to=event_image_upload_to,
        verbose_name="Изображение",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Альтернативный текст",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Порядок",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        db_table = "event_images"
        verbose_name = "Изображение мероприятия"
        verbose_name_plural = "Изображения мероприятий"
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.event} - {self.image.name}"


class OrganizationNews(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="news",
        verbose_name="Организация",
    )
    created_by_member = models.ForeignKey(
        OrganizationMember,
        on_delete=models.CASCADE,
        related_name="created_organization_news",
        verbose_name="Создатель",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
    )
    text = models.TextField(verbose_name="Текст")
    image = models.ImageField(
        upload_to=organization_news_image_upload_to,
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    comments = models.TextField(blank=True, verbose_name="Комментарии")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        db_table = "organization_news"
        verbose_name = "Новость организации"
        verbose_name_plural = "Новости организаций"
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self.created_by_member_id
            and self.organization_id
            and self.created_by_member.organization_id != self.organization_id
        ):
            raise ValidationError(
                {"created_by_member": "Создатель новости должен быть участником этой организации."}
            )


class OrganizationNewsImage(models.Model):
    news = models.ForeignKey(
        OrganizationNews,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Новость",
    )
    image = models.ImageField(
        upload_to=organization_news_gallery_image_upload_to,
        verbose_name="Изображение",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Альтернативный текст",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Порядок",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        db_table = "organization_news_images"
        verbose_name = "Изображение новости организации"
        verbose_name_plural = "Изображения новостей организаций"
        ordering = ("sort_order", "id")

    def __str__(self):
        return f"{self.news} - {self.image.name}"


class OrganizationNewsComment(models.Model):
    news = models.ForeignKey(
        OrganizationNews,
        on_delete=models.CASCADE,
        related_name="comment_items",
        verbose_name="Новость",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_news_comments",
        verbose_name="Автор",
    )
    text = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        db_table = "organization_news_comments"
        verbose_name = "Комментарий к новости"
        verbose_name_plural = "Комментарии к новостям"
        ordering = ("created_at", "id")

    def __str__(self):
        return f"{self.created_by} - {self.news}"


class OrganizationRegistrationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Одобрена"
        REJECTED = "rejected", "Отклонена"

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
    max_url = models.URLField(blank=True, verbose_name="MAX")
    vk_url = models.URLField(blank=True, verbose_name="VK")
    website_url = models.URLField(blank=True, verbose_name="Website")

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_registration_requests"
        verbose_name = "Заявка на регистрацию организации"
        verbose_name_plural = "Заявки на регистрацию организаций"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.official_name} ({self.status})"
