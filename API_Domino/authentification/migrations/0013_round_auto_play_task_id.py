# Generated by Django 5.1.5 on 2025-02-22 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentification', '0012_session_is_public_session_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='round',
            name='auto_play_task_id',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
    ]
