# Generated by Django 2.1.7 on 2019-04-08 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='contractEndDate',
            new_name='dbContractEndDate',
        ),
        migrations.RenameField(
            model_name='company',
            old_name='contractStartDate',
            new_name='dbContractStartDate',
        ),
        migrations.AddField(
            model_name='company',
            name='solutionContractEndDate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='solutionContractStartDate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='companyStatus',
            field=models.CharField(choices=[('Y', 'Y'), ('N', 'N'), ('X', 'X')], default='Y', max_length=1),
        ),
    ]
