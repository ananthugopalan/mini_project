# Generated by Django 5.0.1 on 2024-02-27 09:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agriselect', '0034_order_accepted_by_store'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryAgentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_photo', models.ImageField(blank=True, null=True, upload_to='profile_photos/')),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], max_length=10)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=15)),
                ('location', models.CharField(choices=[('ernakulam', 'Ernakulam'), ('malappuram', 'Malappuram'), ('pathanamthitta', 'Pathanamthitta'), ('kannur', 'Kannur')], max_length=100)),
                ('id_number', models.CharField(max_length=12)),
                ('driver_license_number', models.CharField(max_length=50)),
                ('employee_id', models.CharField(blank=True, max_length=50, null=True)),
                ('date_of_joining', models.DateField()),
                ('vehicle_type', models.CharField(blank=True, max_length=100, null=True)),
                ('vehicle_number', models.CharField(max_length=20)),
                ('bank_name', models.CharField(choices=[('ALLAHABAD BANK', 'Allahabad Bank'), ('ANDHRA BANK', 'Andhra Bank'), ('AXIS BANK', 'Axis Bank'), ('BANK OF BARODA', 'Bank of Baroda'), ('BANK OF INDIA', 'Bank of India'), ('BANK OF MAHARASHTRA', 'Bank of Maharashtra'), ('CANARA BANK', 'Canara Bank'), ('CORPORATION BANK', 'Corporation Bank'), ('HONG KONG & SHANGHAI BANK', 'Hong Kong & Shanghai Bank'), ('INDIAN BANK', 'Indian Bank'), ('INDIAN OVERSEAS BANK', 'Indian Overseas Bank'), ('KARUR VYSYA BANK', 'Karur Vysya Bank'), ('NORTH MALABAR GRAMIN BANK', 'North Malabar Gramin Bank'), ('ORIENTAL BANK OF COMMERCE', 'Oriental Bank of Commerce'), ('PUNJAB AND SIND BANK', 'Punjab and Sind Bank'), ('PUNJAB NATIONAL BANK', 'Punjab National Bank'), ('RESERVE BANK OF INDIA', 'Reserve Bank of India'), ('SOUTH INDIAN BANK', 'South Indian Bank'), ('STANDARD CHARTERED BANK', 'Standard Chartered Bank'), ('STATE BANK OF BIKANER AND JAIPUR', 'State Bank of Bikaner and Jaipur'), ('STATE BANK OF HYDERABAD', 'State Bank of Hyderabad'), ('STATE BANK OF MYSORE', 'State Bank of Mysore'), ('STATE BANK OF PATIALA', 'State Bank of Patiala'), ('STATE BANK OF TRAVANCORE', 'State Bank of Travancore'), ('SYNDICATE BANK', 'Syndicate Bank'), ('LAKSHMI VILAS BANK LTD', 'Lakshmi Vilas Bank Ltd'), ('UCO BANK', 'UCO Bank'), ('UNION BANK OF INDIA', 'Union Bank of India'), ('UNITED BANK OF INDIA', 'United Bank of India'), ('VIJAYA BANK', 'Vijaya Bank'), ('CENTRAL BANK OF INDIA', 'Central Bank of India'), ('DENA BANK', 'Dena Bank'), ('BANDHAN BANK LIMITED', 'Bandhan Bank Limited'), ('KERALA GRAMIN BANK', 'Kerala Gramin Bank'), ('LAXMI VILAS BANK', 'Laxmi Vilas Bank'), ('BANK OF BAHARAIN AND KUWAIT BSC', 'Bank of Baharain and Kuwait BSC'), ('BHARATIYA MAHILA BANK LIMITED', 'Bharatiya Mahila Bank Limited'), ('CATHOLIC SYRIAN BANK', 'Catholic Syrian Bank'), ('CITIBANK NA', 'Citibank NA'), ('CITY UNION BANK LTD', 'City Union Bank Ltd'), ('DEVELOPMENT CREDIT BANK', 'Development Credit Bank'), ('DHANALAXMI BANK', 'Dhanalaxmi Bank'), ('DOHA BANK', 'Doha Bank'), ('FEDERAL BANK LTD', 'Federal Bank Ltd'), ('HDFC BANK LTD', 'HDFC Bank Ltd'), ('ICICI BANK LTD', 'ICICI Bank Ltd'), ('IDBI BANK LTD', 'IDBI Bank Ltd'), ('ING VYSYA BANK LTD', 'ING Vysya Bank Ltd'), ('INDUSIND BANK LTD', 'IndusInd Bank Ltd'), ('JAMMU AND KASHMIR BANK LTD', 'Jammu and Kashmir Bank Ltd'), ('KARNATAKA BANK LTD', 'Karnataka Bank Ltd'), ('KOTAK MAHINDRA BANK', 'Kotak Mahindra Bank'), ('STATE BANK OF INDIA', 'State Bank of India'), ('TAMILNAD MERCANTILE BANK LTD', 'Tamilnad Mercantile Bank Ltd'), ('YES BANK LTD', 'Yes Bank Ltd'), ('OTHER', 'Other')], max_length=100)),
                ('branch', models.CharField(max_length=100)),
                ('account_number', models.CharField(max_length=18)),
                ('ifsc_code', models.CharField(max_length=11)),
                ('delivery_agent', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
