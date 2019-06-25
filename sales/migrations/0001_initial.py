# Generated by Django 2.1.7 on 2019-06-25 16:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hr', '0001_initial'),
        ('client', '0001_initial'),
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
                ('saleType', models.CharField(choices=[('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'), ('기타', '기타')], default='직판', max_length=10)),
                ('saleIndustry', models.CharField(choices=[('금융', '금융'), ('공공', '공공'), ('유통 & 제조', '유통 & 제조'), ('통신 & 미디어', '통신 & 미디어'), ('기타', '기타')], default='금융', max_length=10)),
                ('mainCategory', models.CharField(max_length=50)),
                ('subCategory', models.CharField(max_length=50)),
                ('salePrice', models.BigIntegerField()),
                ('profitPrice', models.BigIntegerField()),
                ('profitRatio', models.FloatField()),
                ('contractDate', models.DateField()),
                ('contractStep', models.CharField(choices=[('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop')], default='Opportunity', max_length=20)),
                ('contractStartDate', models.DateField(blank=True, null=True)),
                ('contractEndDate', models.DateField(blank=True, null=True)),
                ('depositCondition', models.CharField(blank=True, choices=[('계산서 발행 후', '계산서 발행 후'), ('당월', '당월'), ('익월', '익월'), ('당월 말', '당월 말'), ('익월 초', '익월 초'), ('익월 말', '익월 말')], default='계산서 발행 후', max_length=20, null=True)),
                ('depositConditionDay', models.IntegerField(blank=True, default=0, null=True)),
                ('contractPaper', models.FileField(blank=True, null=True, upload_to='contractPaper/%Y_%m')),
                ('orderPaper', models.FileField(blank=True, null=True, upload_to='orderPaper/%Y_%m')),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
                ('endCompanyName', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='endCompanyName', to='client.Company')),
                ('saleCompanyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saleCompanyName', to='client.Company')),
                ('saleCustomerId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saleCustomerId', to='client.Customer')),
                ('transferContractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='Contractitem',
            fields=[
                ('contractItemId', models.AutoField(primary_key=True, serialize=False)),
                ('mainCategory', models.CharField(max_length=50)),
                ('subCategory', models.CharField(max_length=50)),
                ('itemName', models.CharField(max_length=50)),
                ('itemPrice', models.BigIntegerField()),
                ('contractId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('goalId', models.AutoField(primary_key=True, serialize=False)),
                ('empDeptName', models.CharField(max_length=30)),
                ('empName', models.CharField(max_length=30)),
                ('year', models.BigIntegerField()),
                ('sales1', models.BigIntegerField()),
                ('sales2', models.BigIntegerField()),
                ('sales3', models.BigIntegerField()),
                ('sales4', models.BigIntegerField()),
                ('sales5', models.BigIntegerField()),
                ('sales6', models.BigIntegerField()),
                ('sales7', models.BigIntegerField()),
                ('sales8', models.BigIntegerField()),
                ('sales9', models.BigIntegerField()),
                ('sales10', models.BigIntegerField()),
                ('sales11', models.BigIntegerField()),
                ('sales12', models.BigIntegerField()),
                ('salesq1', models.BigIntegerField()),
                ('salesq2', models.BigIntegerField()),
                ('salesq3', models.BigIntegerField()),
                ('salesq4', models.BigIntegerField()),
                ('profit1', models.BigIntegerField()),
                ('profit2', models.BigIntegerField()),
                ('profit3', models.BigIntegerField()),
                ('profit4', models.BigIntegerField()),
                ('profit5', models.BigIntegerField()),
                ('profit6', models.BigIntegerField()),
                ('profit7', models.BigIntegerField()),
                ('profit8', models.BigIntegerField()),
                ('profit9', models.BigIntegerField()),
                ('profit10', models.BigIntegerField()),
                ('profit11', models.BigIntegerField()),
                ('profit12', models.BigIntegerField()),
                ('profitq1', models.BigIntegerField()),
                ('profitq2', models.BigIntegerField()),
                ('profitq3', models.BigIntegerField()),
                ('profitq4', models.BigIntegerField()),
                ('yearSalesSum', models.BigIntegerField()),
                ('yearProfitSum', models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('purchaseId', models.AutoField(primary_key=True, serialize=False)),
                ('purchasePrice', models.BigIntegerField()),
                ('predictBillingDate', models.DateField(blank=True, null=True)),
                ('billingDate', models.DateField(blank=True, null=True)),
                ('predictWithdrawDate', models.DateField(blank=True, null=True)),
                ('withdrawDate', models.DateField(blank=True, null=True)),
                ('billingTime', models.CharField(blank=True, max_length=10, null=True)),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('contractId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
                ('purchaseCompany', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
            ],
        ),
        migrations.CreateModel(
            name='Revenue',
            fields=[
                ('revenueId', models.AutoField(primary_key=True, serialize=False)),
                ('revenuePrice', models.BigIntegerField()),
                ('revenueProfitPrice', models.BigIntegerField()),
                ('revenueProfitRatio', models.FloatField()),
                ('predictBillingDate', models.DateField(blank=True, null=True)),
                ('billingDate', models.DateField(blank=True, null=True)),
                ('predictDepositDate', models.DateField(blank=True, null=True)),
                ('depositDate', models.DateField(blank=True, null=True)),
                ('billingTime', models.CharField(blank=True, max_length=10, null=True)),
                ('comment', models.CharField(blank=True, max_length=200, null=True)),
                ('contractId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Contract')),
                ('revenueCompany', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
            ],
        ),
    ]
