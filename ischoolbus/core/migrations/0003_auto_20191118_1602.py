# Generated by Django 2.2.3 on 2019-11-18 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_bussupervisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='avatar',
            field=models.FileField(default=None, upload_to='avatar/parent'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='birthday',
            field=models.DateField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='district',
            field=models.CharField(default=None, max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='first_name',
            field=models.CharField(default=None, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='home_number',
            field=models.CharField(default=None, max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='last_name',
            field=models.CharField(default=None, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='phone_number',
            field=models.CharField(default=None, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='province',
            field=models.CharField(default=None, max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parent',
            name='ward',
            field=models.CharField(default=None, max_length=250),
            preserve_default=False,
        ),
    ]
