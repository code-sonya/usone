# Generated by Django 2.1.5 on 2019-03-26 02:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hr', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('companyName', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('companyAddress', models.CharField(max_length=200)),
                ('companyLatitude', models.FloatField(blank=True, null=True)),
                ('companyLongitude', models.FloatField(blank=True, null=True)),
                ('companyDbms', models.TextField(blank=True, null=True)),
                ('companySystem', models.TextField(blank=True, null=True)),
                ('dbComment', models.TextField(blank=True, null=True)),
                ('solutionComment', models.TextField(blank=True, null=True)),
                ('contractStartDate', models.DateField(blank=True, null=True)),
                ('contractEndDate', models.DateField(blank=True, null=True)),
                ('companyStatus', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=1)),
                ('dbMainEmpId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dbMainEmpId', to='hr.Employee')),
                ('dbSubEmpId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dbSubEmpId', to='hr.Employee')),
                ('saleEmpId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saleEmpID', to='hr.Employee')),
                ('solutionMainEmpId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solutionMainEmpID', to='hr.Employee')),
                ('solutionSubEmpId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solutionSubEmpId', to='hr.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customerName', models.CharField(max_length=10)),
                ('customerDeptName', models.CharField(blank=True, max_length=30, null=True)),
                ('customerPhone', models.CharField(blank=True, max_length=20, null=True)),
                ('customerEmail', models.EmailField(max_length=254)),
                ('customerStatus', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=1)),
                ('companyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='customer',
            unique_together={('customerName', 'companyName')},
        ),
    ]
