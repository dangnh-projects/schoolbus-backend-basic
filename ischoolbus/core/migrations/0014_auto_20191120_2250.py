# Generated by Django 2.2.3 on 2019-11-20 15:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20191120_2249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='parent',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Parent'),
        ),
    ]
