# Generated by Django 3.0.5 on 2020-04-16 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0020_package_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='rank',
            field=models.PositiveIntegerField(db_index=True, default=0, verbose_name='rank'),
        ),
        migrations.AlterField(
            model_name='release',
            name='status',
            field=models.CharField(choices=[('new', 'new'), ('done', 'done')], db_index=True, default='new', max_length=50, verbose_name='status'),
        ),
    ]
