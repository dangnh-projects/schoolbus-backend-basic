# Generated by Django 2.1.7 on 2019-12-12 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_busroutewithlocation_delay_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='busroutewithlocation',
            name='delay_time',
            field=models.CharField(default='0', max_length=100),
        ),
    ]
