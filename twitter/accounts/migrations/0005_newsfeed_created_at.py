# Generated by Django 4.0.6 on 2022-07-27 23:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_newsfeed_to_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="newsfeed",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
