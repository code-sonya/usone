# Generated by Django 2.1.7 on 2019-10-28 00:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('client', '0001_initial'),
        ('hr', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='dbMainEmpId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dbMainEmpId', to='hr.Employee'),
        ),
        migrations.AddField(
            model_name='company',
            name='dbSubEmpId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dbSubEmpId', to='hr.Employee'),
        ),
        migrations.AddField(
            model_name='company',
            name='saleEmpId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saleEmpID', to='hr.Employee'),
        ),
        migrations.AddField(
            model_name='company',
            name='solutionMainEmpId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solutionMainEmpID', to='hr.Employee'),
        ),
        migrations.AddField(
            model_name='company',
            name='solutionSubEmpId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solutionSubEmpId', to='hr.Employee'),
        ),
        migrations.AlterUniqueTogether(
            name='customer',
            unique_together={('customerName', 'companyName')},
        ),
    ]
