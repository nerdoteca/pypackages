# Generated by Django 3.0.4 on 2020-04-06 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0003_delete_log'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='status',
            field=models.CharField(choices=[('new', 'new'), ('tweeted', 'tweeted')], db_index=True, default='new', max_length=50, verbose_name='status'),
        ),
    ]
