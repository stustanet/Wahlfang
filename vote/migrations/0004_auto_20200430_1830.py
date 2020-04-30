# Generated by Django 3.0.5 on 2020-04-30 16:30
from datetime import datetime

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0003_auto_20200430_1807'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='description',
        ),
        migrations.AddField(
            model_name='election',
            name='meeting_link',
            field=models.CharField(default='https://meet.stusta.de', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='election',
            name='meeting_start_time',
            field=models.DateTimeField(default=datetime.strptime("2020-05-15 18:00:00+02:00", "%Y-%m-%d %H:%M:%S%z")),
            preserve_default=False,
        ),
    ]