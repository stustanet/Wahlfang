# Generated by Django 3.0.6 on 2020-05-31 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0007_auto_20200530_2113'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='result_published',
            field=models.CharField(choices=[('0', 'unpublished'), ('1', 'only winners published'), ('2', 'fully published')], default='0', max_length=1),
        ),
    ]