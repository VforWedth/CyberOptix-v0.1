#!/usr/bin/env python
import os
import sys
import django
from django.core import serializers
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))
django.setup()

# Import models
from userauths.models import User
from flame.models import Category, Brand, Product, CartOrder, CartOrderItem, Address, Shop, Wishlist, ProductReview

def export_model_data(model, filename):
    try:
        data = serializers.serialize('json', model.objects.all(), indent=2, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        print(f"Exported {model.objects.count()} {model.__name__} records to {filename}")
        return True
    except Exception as e:
        print(f"Error exporting {model.__name__}: {e}")
        return False

# Export each model separately
models_to_export = [
    (User, 'userauths_data.json'),
    (Category, 'categories_data.json'),
    (Brand, 'brands_data.json'),
    (Product, 'products_data.json'),
    (CartOrder, 'orders_data.json'),
    (CartOrderItem, 'order_items_data.json'),
    (Address, 'addresses_data.json'),
    (Shop, 'shops_data.json'),
    (Wishlist, 'wishlist_data.json'),
    (ProductReview, 'reviews_data.json'),
]

print("Starting data export from SQLite...")
successful_exports = 0

for model, filename in models_to_export:
    if export_model_data(model, filename):
        successful_exports += 1

print(f"\nExport completed: {successful_exports}/{len(models_to_export)} models exported successfully")