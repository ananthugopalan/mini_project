# Generated by Django 5.0.1 on 2024-02-28 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agriselect', '0036_rename_id_number_deliveryagentprofile_aadhaar_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryagentprofile',
            name='id_document',
            field=models.FileField(blank=True, null=True, upload_to='id_documents/'),
        ),
    ]
