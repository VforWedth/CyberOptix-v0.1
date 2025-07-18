# Generated by Django 5.1.4 on 2025-04-26 19:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0019_product_stock_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartorder',
            name='order_type',
            field=models.CharField(choices=[('home', 'Home'), ('shop', 'Shop')], default='home', max_length=10),
        ),
        migrations.AddField(
            model_name='cartorder',
            name='shop',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='flame.shop'),
        ),
        migrations.AddField(
            model_name='shop',
            name='paypal_email',
            field=models.EmailField(default='lorendrain47@gmail.com', max_length=254),
        ),
    ]
