# Generated by Django 5.0 on 2024-05-08 15:42

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agriselect', '0062_growbag_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='growbag',
            name='order_date_only',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='growbag',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('successful', 'Successful'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='growbag',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
