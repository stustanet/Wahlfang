# Generated by Django 3.0.5 on 2020-05-24 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0007_auto_20200516_1814'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElectionManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('elections', models.ManyToManyField(blank=True, related_name='managers', to='vote.Election')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
