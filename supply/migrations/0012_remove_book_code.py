# Generated by Django 2.1.7 on 2020-03-12 15:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('supply', '0011_book_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='code',
        ),
    ]