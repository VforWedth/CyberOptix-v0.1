# Generated by Django 5.1.4 on 2025-04-24 06:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0016_new_shop_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_products', to='flame.shop'),
        ),
    ]
