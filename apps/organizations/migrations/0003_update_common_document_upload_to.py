import apps.organizations.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_trim_organization_required_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="charter_document",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Устав",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="egrul_extract",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Выписка из ЕГРЮЛ",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="executive_passport_copy",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="founders_appointment_decision",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="inn_certificate",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Свидетельство о присвоении ИНН",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="nko_registry_notice",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении",
            ),
        ),
        migrations.AlterField(
            model_name="organization",
            name="state_registration_certificate",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="charter_document",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Устав",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="egrul_extract",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Выписка из ЕГРЮЛ",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="executive_passport_copy",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Копия паспорта лица, осуществляющего функции единоличного исполнительного органа",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="founders_appointment_decision",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Решение учредителей о назначении высшего коллегиального и исполнительного органа",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="inn_certificate",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Свидетельство о присвоении ИНН",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="nko_registry_notice",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Уведомление о включении в реестр НКО / Письмо-подтверждение о не включении",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="official_name",
            field=models.CharField(
                max_length=255,
                verbose_name="Официальное название организации",
            ),
        ),
        migrations.AlterField(
            model_name="organizationregistrationrequest",
            name="state_registration_certificate",
            field=models.FileField(
                upload_to=apps.organizations.models.organization_common_document_upload_to,
                verbose_name="Свидетельство о гос регистрации ЮЛ / Свидетельство о регистрации НКО",
            ),
        ),
    ]
