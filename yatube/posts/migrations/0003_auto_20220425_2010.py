# Generated by Django 2.2.9 on 2022-04-25 13:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220425_1715'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='discription',
            new_name='description',
        ),
    ]
