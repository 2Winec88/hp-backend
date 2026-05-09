import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("collections", "0010_poll_finalized_at_poll_finalized_by_member_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DonorGroupMeeting",
            new_name="DonorGroupParameters",
        ),
        migrations.AlterModelOptions(
            name="donorgroupparameters",
            options={
                "ordering": ("-finalized_at", "-id"),
                "verbose_name": "Donor group parameters",
                "verbose_name_plural": "Donor group parameters",
            },
        ),
        migrations.AlterField(
            model_name="donorgroupparameters",
            name="donor_group",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="parameters",
                to="collections.donorgroup",
            ),
        ),
        migrations.AlterField(
            model_name="donorgroupparameters",
            name="finalized_by_member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="finalized_donor_group_parameters",
                to="organizations.organizationmember",
            ),
        ),
        migrations.AlterField(
            model_name="donorgroupparameters",
            name="geodata",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="donor_group_parameters",
                to="common.geodata",
            ),
        ),
    ]
