# Generated by Django 2.1.2 on 2018-11-01 16:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SecureBank', '0006_auto_20181101_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='Employee',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='SecureBank.BankUser'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='FromAccount',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='FromAccount', to='SecureBank.Account'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='ToAccount',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ToAccount', to='SecureBank.Account'),
        ),
    ]