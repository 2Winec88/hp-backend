from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="scope",
            field=models.CharField(
                choices=[
                    ("event", "Мероприятия"),
                    ("fundraising", "Сборы"),
                ],
                default="event",
                max_length=20,
                verbose_name="Область",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(
                allow_unicode=True,
                blank=True,
                max_length=100,
                verbose_name="Slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("scope", "name"),
                name="unique_category_name_per_scope",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("scope", "slug"),
                name="unique_category_slug_per_scope",
            ),
        ),
    ]
