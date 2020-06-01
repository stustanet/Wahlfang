# Generated by Django 3.0.5 on 2020-05-31 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0011_voter_logged_in'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='result_published',
            field=models.CharField(choices=[('0', 'unpublished'), ('1', 'fully published')], default='0', max_length=1),
        ),
    ]