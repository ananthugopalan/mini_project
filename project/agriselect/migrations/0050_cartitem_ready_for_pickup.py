# Generated by Django 5.0.1 on 2024-03-05 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agriselect', '0049_order_ready_for_pickup'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='ready_for_pickup',
            field=models.BooleanField(default=False),
        ),
    ]
