# Generated by Django 2.1.7 on 2019-11-11 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0001_initial'),
        ('approval', '0003_auto_20191101_1351'),
    ]

    operations = [
        migrations.CreateModel(
            name='Approvalform',
            fields=[
                ('approvalId', models.AutoField(primary_key=True, serialize=False)),
                ('approvalStep', models.IntegerField(default=0)),
                ('approvalCategory', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='approval.Approvalcategory')),
                ('approvalEmp', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hr.Employee')),
                ('formId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='approval.Documentform')),
            ],
        ),
        migrations.AddField(
            model_name='documentfile',
            name='documentId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='approval.Document'),
        ),
    ]
