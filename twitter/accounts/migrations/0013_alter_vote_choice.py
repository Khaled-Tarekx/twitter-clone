# Generated by Django 4.0.6 on 2022-09-01 12:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_alter_likes_reply_alter_likes_tweet"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vote",
            name="choice",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="votes",
                to="accounts.choice",
            ),
        ),
    ]
