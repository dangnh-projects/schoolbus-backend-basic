# Generated by Django 2.2.4 on 2019-11-21 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_remove_parent_id_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='busroute',
            name='end_time',
            field=models.DateTimeField(default=None),
        ),
        migrations.AddField(
            model_name='busroute',
            name='start_time',
            field=models.DateTimeField(default=None),
        ),
        migrations.DeleteModel(
            name='Schedule',
        ),
    ]