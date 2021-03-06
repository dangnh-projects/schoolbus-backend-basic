# Generated by Django 2.1.7 on 2020-02-17 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_parent_preferred_langage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.IntegerField(blank=True, editable=False, null=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('updated_by', models.IntegerField(blank=True, editable=False, null=True)),
                ('name', models.CharField(max_length=200)),
                ('relationship', models.CharField(max_length=200)),
                ('phone', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='student',
            name='additional_contact_info',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='contact', to='core.Contact'),
        ),
        migrations.RenameField(
            model_name='student',
            old_name='bus_registerd_date',
            new_name='bus_registered_date',
        ),
        migrations.RenameField(
            model_name='parent',
            old_name='preferred_langage',
            new_name='preferred_language',
        ),
    ]
