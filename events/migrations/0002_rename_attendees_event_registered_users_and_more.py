# Generated by Django 5.1.1 on 2024-10-08 14:18

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='attendees',
            new_name='registered_users',
        ),
        migrations.AlterField(
            model_name='event',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
