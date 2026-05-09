# Generated manually to move CourierProfile state from collections to accounts.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_courierprofile"),
        ("collections", "0008_donorgroupmeeting"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="CourierProfile"),
            ],
        ),
    ]
