# Generated by Django 5.1.5 on 2025-01-28 22:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentification', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='round_id',
        ),
    ]
