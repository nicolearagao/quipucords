# Generated by Django 3.2.17 on 2023-03-21 08:19

from django.db import migrations, models

from api.inspectresult.model import RawFactEncoder


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0028_alter_source_credentials"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rawfact",
            name="value",
            field=models.JSONField(encoder=RawFactEncoder, null=True),
        ),
    ]
