# Generated by Django 2.1.7 on 2019-11-28 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0008_purchasetyped'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasetypeb',
            name='classification',
            field=models.CharField(choices=[('상품_HW', '상품_HW'), ('상품_SW', '상품_SW'), ('유지보수_HW', '유지보수_HW'), ('유지보수_SW', '유지보수_SW'), ('PM상주', 'PM상주'), ('기타', '기타')], max_length=20),
        ),
        migrations.AlterField(
            model_name='purchasetypec',
            name='classification',
            field=models.CharField(choices=[('상품_HW', '상품_HW'), ('상품_SW', '상품_SW'), ('유지보수_HW', '유지보수_HW'), ('유지보수_SW', '유지보수_SW'), ('HW', 'HW'), ('SW', 'SW'), ('PM상주', 'PM상주'), ('프로젝트비용', '프로젝트비용'), ('사업진행비용', '사업진행비용'), ('교육', '교육'), ('교육쿠폰', '교육쿠폰'), ('부자재매입', '부자재매입'), ('기타', '기타')], max_length=20),
        ),
    ]
