# Generated by Django 2.1.7 on 2020-01-16 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_auto_20200115_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='preferred_langage',
            field=models.CharField(default='en-US', max_length=100),
        ),
    ]