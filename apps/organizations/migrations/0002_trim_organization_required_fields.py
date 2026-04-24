from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="organizationregistrationrequest",
            old_name="name",
            new_name="official_name",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="description",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="postal_address",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="website",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="statistics_letter",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="supervisory_board_decision",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="charity_program",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="annual_property_report",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="accounting_statements",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="personal_data_consent",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="description",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="postal_address",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="website",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="statistics_letter",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="supervisory_board_decision",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="charity_program",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="annual_property_report",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="accounting_statements",
        ),
        migrations.RemoveField(
            model_name="organizationregistrationrequest",
            name="personal_data_consent",
        ),
    ]
