# Generated by Django 2.1.7 on 2020-01-15 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0061_auto_20200115_1009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtemplate',
            name='notification_type',
            field=models.IntegerField(),
        ),
    ]
