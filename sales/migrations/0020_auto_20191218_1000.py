# Generated by Django 2.1.7 on 2019-12-18 10:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0019_auto_20191216_1424'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchaseorderform',
            fields=[
                ('formId', models.AutoField(primary_key=True, serialize=False)),
                ('formNumber', models.IntegerField(default=0)),
                ('formTitle', models.CharField(max_length=200)),
                ('formHtml', models.TextField()),
                ('comment', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='sendCount',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='formId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Purchaseorderform'),
        ),
    ]
