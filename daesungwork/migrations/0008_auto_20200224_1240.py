# Generated by Django 2.1.7 on 2020-02-24 12:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0007_auto_20200210_1414'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('productId', models.AutoField(primary_key=True, serialize=False)),
                ('modelName', models.CharField(max_length=20, unique=True)),
                ('productName', models.CharField(blank=True, max_length=20, null=True)),
                ('unitPrice', models.IntegerField(blank=True, null=True)),
                ('productPicture', models.FileField(upload_to='product/')),
            ],
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('sizeId', models.AutoField(primary_key=True, serialize=False)),
                ('size', models.CharField(blank=True, max_length=10, null=True)),
                ('productId', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='daesungwork.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('warehouseId', models.AutoField(primary_key=True, serialize=False)),
                ('warehouseDrawing', models.FileField(upload_to='warehouse/')),
            ],
        ),
        migrations.CreateModel(
            name='WarehouseMainCategory',
            fields=[
                ('categoryId', models.AutoField(primary_key=True, serialize=False)),
                ('categoryName', models.CharField(max_length=20, unique=True)),
                ('categoryStatus', models.CharField(choices=[('Y', '사용'), ('N', '미사용')], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='WarehouseSubCategory',
            fields=[
                ('categoryId', models.AutoField(primary_key=True, serialize=False)),
                ('categoryName', models.CharField(max_length=20, unique=True)),
                ('categoryStatus', models.CharField(choices=[('Y', '사용'), ('N', '미사용')], max_length=20)),
            ],
        ),
        migrations.AddField(
            model_name='warehouse',
            name='mainCategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='daesungwork.WarehouseMainCategory'),
        ),
        migrations.AddField(
            model_name='warehouse',
            name='subCategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='daesungwork.WarehouseSubCategory'),
        ),
        migrations.AddField(
            model_name='product',
            name='position',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='daesungwork.Warehouse'),
        ),
    ]
