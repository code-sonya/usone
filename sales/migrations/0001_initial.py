# Generated by Django 2.1.7 on 2019-05-17 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('client', '0001_initial'),
        ('hr', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('categoryId', models.AutoField(primary_key=True, serialize=False)),
                ('mainCategory', models.CharField(max_length=50)),
                ('subCategory', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('contractId', models.AutoField(primary_key=True, serialize=False)),
                ('contractCode', models.CharField(max_length=30)),
                ('contractName', models.CharField(max_length=200)),
                ('empName', models.CharField(max_length=10)),
                ('empDeptName', models.CharField(max_length=30)),
                ('saleCustomerName', models.CharField(blank=True, max_length=10, null=True)),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('saleType', models.CharField(choices=[('직판', '직판'), ('T1', 'T1'), ('T2', 'T2')], default='직판', max_length=10)),
                ('saleIndustry', models.CharField(choices=[('금융', '금융'), ('공공', '공공'), ('제조', '제조'), ('통신', '통신'), ('기타', '기타')], default='금융', max_length=10)),
                ('salePrice', models.IntegerField()),
                ('profitPrice', models.IntegerField()),
                ('profitRatio', models.FloatField()),
                ('contractDate', models.DateField()),
                ('contractStep', models.CharField(choices=[('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop')], default='Opportunity', max_length=20)),
                ('contractStartDate', models.DateField(blank=True, null=True)),
                ('contractEndDate', models.DateField(blank=True, null=True)),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
                ('endCompanyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='endCompanyName', to='client.Company')),
                ('saleCompanyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saleCompanyName', to='client.Company')),
                ('saleCustomerId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saleCustomerId', to='client.Customer')),
            ],
        ),
        migrations.CreateModel(
            name='Contractitem',
            fields=[
                ('contractItemId', models.AutoField(primary_key=True, serialize=False)),
                ('mainCategory', models.CharField(max_length=50)),
                ('subCategory', models.CharField(max_length=50)),
                ('itemName', models.CharField(max_length=50)),
                ('itemPrice', models.IntegerField()),
                ('contractId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('goalId', models.AutoField(primary_key=True, serialize=False)),
                ('empDeptName', models.CharField(max_length=30)),
                ('empName', models.CharField(max_length=30)),
                ('year', models.IntegerField()),
                ('jan', models.IntegerField()),
                ('feb', models.IntegerField()),
                ('mar', models.IntegerField()),
                ('apr', models.IntegerField()),
                ('may', models.IntegerField()),
                ('jun', models.IntegerField()),
                ('jul', models.IntegerField()),
                ('aug', models.IntegerField()),
                ('sep', models.IntegerField()),
                ('oct', models.IntegerField()),
                ('nov', models.IntegerField()),
                ('dec', models.IntegerField()),
                ('q1', models.IntegerField()),
                ('q2', models.IntegerField()),
                ('q3', models.IntegerField()),
                ('q4', models.IntegerField()),
                ('yearSum', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Revenue',
            fields=[
                ('revenueId', models.AutoField(primary_key=True, serialize=False)),
                ('revenuePrice', models.IntegerField()),
                ('revenueProfitPrice', models.IntegerField()),
                ('billingDate', models.DateField(blank=True, null=True)),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('contractId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
            ],
        ),
    ]