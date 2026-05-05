from django.conf import settings
from django.db import migrations, models

import apps.organizations.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="РќР°Р·РІР°РЅРёРµ")),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        blank=True,
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("event", "РњРµСЂРѕРїСЂРёСЏС‚РёСЏ"),
                            ("fundraising", "РЎР±РѕСЂС‹"),
                        ],
                        max_length=20,
                        verbose_name="РћР±Р»Р°СЃС‚СЊ",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="РћРїРёСЃР°РЅРёРµ")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="РЎРѕР·РґР°РЅРѕ"),
                ),
            ],
            options={
                "verbose_name": "РљР°С‚РµРіРѕСЂРёСЏ",
                "verbose_name_plural": "РљР°С‚РµРіРѕСЂРёРё",
                "db_table": "categories",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("official_name", models.CharField(max_length=255, verbose_name="Официальное название организации")),
                ("description", models.TextField(blank=True, verbose_name="Описание организации")),
                ("legal_address", models.CharField(max_length=500, verbose_name="Юридический адрес")),
                ("postal_address", models.CharField(blank=True, max_length=500, verbose_name="Почтовый адрес")),
                ("phone", models.CharField(max_length=50, verbose_name="Телефон")),
                ("email", models.EmailField(max_length=254, verbose_name="Email")),
                ("website", models.URLField(blank=True, verbose_name="Адрес веб-сайта")),
                ("executive_person_full_name", models.CharField(max_length=255, verbose_name="ФИО исполнительного лица")),
                ("executive_authority_basis", models.CharField(max_length=500, verbose_name="Действующий на основании")),
                ("executive_body_name", models.CharField(max_length=255, verbose_name="Наименование исполнительного органа")),
                ("charter_document", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Устав")),
                ("inn_certificate", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Свидетельство о присвоении ИНН")),
                ("statistics_letter", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Информационное письмо органов статистики о присвоении кодов")),
                ("state_registration_certificate", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО")),
                ("founders_appointment_decision", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа")),
                ("executive_passport_copy", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа")),
                ("supervisory_board_decision", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Решение учредителей о назначении попечительского совета")),
                ("egrul_extract", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Выписка из ЕГРЮЛ")),
                ("nko_registry_notice", models.FileField(upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении")),
                ("charity_program", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Благотворительная программа фонда на календарный год")),
                ("annual_property_report", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Ежегодный отчёт фонда об использовании имущества за предшествующий год")),
                ("accounting_statements", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_document_upload_to, verbose_name="Бухгалтерская отчетность фонда за предшествующий год")),
                ("personal_data_consent", models.BooleanField(default=False, verbose_name="Согласие на обработку персональных данных")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="created_organizations", to=settings.AUTH_USER_MODEL, verbose_name="Создатель")),
            ],
            options={
                "verbose_name": "Организация",
                "verbose_name_plural": "Организации",
                "db_table": "organizations",
                "ordering": ("official_name",),
            },
        ),
        migrations.CreateModel(
            name="OrganizationMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("manager", "Менеджер"), ("member", "Участник")], default="member", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="members", to="organizations.organization")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="organization_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Участник организации",
                "verbose_name_plural": "Участники организаций",
                "db_table": "organization_members",
            },
        ),
        migrations.CreateModel(
            name="OrganizationRegistrationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название организации")),
                ("description", models.TextField(blank=True, verbose_name="Описание организации")),
                ("legal_address", models.CharField(max_length=500, verbose_name="Юридический адрес")),
                ("postal_address", models.CharField(blank=True, max_length=500, verbose_name="Почтовый адрес")),
                ("phone", models.CharField(max_length=50, verbose_name="Телефон")),
                ("email", models.EmailField(max_length=254, verbose_name="Email")),
                ("website", models.URLField(blank=True, verbose_name="Адрес веб-сайта")),
                ("executive_person_full_name", models.CharField(max_length=255, verbose_name="ФИО исполнительного лица")),
                ("executive_authority_basis", models.CharField(max_length=500, verbose_name="Действующий на основании")),
                ("executive_body_name", models.CharField(max_length=255, verbose_name="Наименование исполнительного органа")),
                ("charter_document", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Устав")),
                ("inn_certificate", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Свидетельство о присвоении ИНН")),
                ("statistics_letter", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Информационное письмо органов статистики о присвоении кодов")),
                ("state_registration_certificate", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО")),
                ("founders_appointment_decision", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа")),
                ("executive_passport_copy", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа")),
                ("supervisory_board_decision", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Решение учредителей о назначении попечительского совета")),
                ("egrul_extract", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Выписка из ЕГРЮЛ")),
                ("nko_registry_notice", models.FileField(upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении")),
                ("charity_program", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Благотворительная программа фонда на календарный год")),
                ("annual_property_report", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Ежегодный отчёт фонда об использовании имущества за предшествующий год")),
                ("accounting_statements", models.FileField(blank=True, null=True, upload_to=apps.organizations.models.organization_request_document_upload_to, verbose_name="Бухгалтерская отчетность фонда за предшествующий год")),
                ("personal_data_consent", models.BooleanField(default=False, verbose_name="Согласие на обработку персональных данных")),
                ("status", models.CharField(choices=[("pending", "На рассмотрении"), ("approved", "Одобрена"), ("rejected", "Отклонена")], default="pending", max_length=20)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="organization_registration_requests", to=settings.AUTH_USER_MODEL)),
                ("organization", models.OneToOneField(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="registration_request", to="organizations.organization")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="reviewed_organization_registration_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Заявка на регистрацию организации",
                "verbose_name_plural": "Заявки на регистрацию организаций",
                "db_table": "organization_registration_requests",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="organizationmember",
            constraint=models.UniqueConstraint(fields=("organization", "user"), name="unique_organization_member"),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(fields=("scope", "name"), name="unique_category_name_per_scope"),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(fields=("scope", "slug"), name="unique_category_slug_per_scope"),
        ),
    ]
