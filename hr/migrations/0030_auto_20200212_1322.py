# Generated by Django 2.1.7 on 2020-02-12 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0029_auto_20200131_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='dispatchCompany',
            field=models.CharField(blank=True, default='내근', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empAnnualLeave',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empAuth',
            field=models.CharField(blank=True, default='일반', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empEmail',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empPhone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empRank',
            field=models.IntegerField(blank=True, default=10, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empRewardAvailable',
            field=models.CharField(blank=True, choices=[('가능', '가능'), ('불가능', '불가능')], default='가능', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empSalary',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empSpecialLeave',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empStamp',
            field=models.FileField(blank=True, default='stamp/accepted.png', null=True, upload_to='stamp/'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empStatus',
            field=models.CharField(blank=True, choices=[('Y', '재직'), ('N', '퇴사')], default='Y', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='message',
            field=models.CharField(blank=True, default='내근 업무 내용을 작성해 주세요.', help_text='내근 업무 내용을 작성해 주세요.', max_length=200, null=True),
        ),
    ]
