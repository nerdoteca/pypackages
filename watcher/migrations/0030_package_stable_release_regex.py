# Generated by Django 3.0.5 on 2020-04-22 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0029_auto_20200421_2038'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='stable_release_regex',
            field=models.CharField(default='', max_length=30, verbose_name='stable release regex'),
        ),
    ]