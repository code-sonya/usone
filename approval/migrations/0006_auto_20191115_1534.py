# Generated by Django 2.1.7 on 2019-11-15 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0005_documentform_approvalformat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='approval',
            name='approvalCategory',
            field=models.CharField(choices=[('신청', '신청'), ('처리', '처리'), ('참조', '참조'), ('결재', '결재'), ('합의', '합의'), ('재무합의', '재무합의')], default='신청', max_length=20),
        ),
        migrations.AlterField(
            model_name='approvalform',
            name='approvalCategory',
            field=models.CharField(default='처리', max_length=10),
        ),
        migrations.DeleteModel(
            name='Approvalcategory',
        ),
    ]