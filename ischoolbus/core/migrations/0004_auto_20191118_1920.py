# Generated by Django 2.2.4 on 2019-11-18 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20191118_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='classroom',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='dob',
            field=models.DateField(default=None),
        ),
    ]