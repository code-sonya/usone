# Generated by Django 2.1.7 on 2019-12-23 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0002_auto_20191206_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='empManager',
            field=models.CharField(choices=[('Y', '부서장'), ('N', '팀원')], default='N', max_length=1),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empStatus',
            field=models.CharField(choices=[('Y', '재직'), ('N', '퇴사')], default='Y', max_length=1),
        ),
    ]
