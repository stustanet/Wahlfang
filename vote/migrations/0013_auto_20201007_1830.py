# Generated by Django 3.0.6 on 2020-10-07 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0012_auto_20200601_0047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
