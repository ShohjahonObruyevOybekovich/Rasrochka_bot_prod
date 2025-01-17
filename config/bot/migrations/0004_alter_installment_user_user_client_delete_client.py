# Generated by Django 5.1.4 on 2024-12-14 10:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_client_alter_installment_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='bot.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='client',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Client',
        ),
    ]
