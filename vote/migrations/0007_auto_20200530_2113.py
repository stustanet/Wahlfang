# Generated by Django 3.0.6 on 2020-05-30 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0006_auto_20200530_1836'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='first_name',
            new_name='display_name',
        ),
        migrations.RemoveField(
            model_name='application',
            name='last_name',
        ),
    ]
