from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_is_email_verified"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Role",
                "verbose_name_plural": "Roles",
                "db_table": "roles",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("role", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="user_roles", to="accounts.role")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="user_roles", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "User role",
                "verbose_name_plural": "User roles",
                "db_table": "user_roles",
            },
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_courier",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_moderator",
        ),
        migrations.AddField(
            model_name="user",
            name="roles",
            field=models.ManyToManyField(blank=True, related_name="users", through="accounts.UserRole", to="accounts.role"),
        ),
        migrations.AddConstraint(
            model_name="userrole",
            constraint=models.UniqueConstraint(fields=("user", "role"), name="unique_user_role"),
        ),
    ]
