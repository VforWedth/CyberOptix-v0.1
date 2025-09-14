#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command
from django.contrib.auth.models import Group

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
sys.path.append(os.path.join(os.path.dirname(__file__), 'inferno'))
django.setup()

def import_data():
    print("Starting data import into PostgreSQL...")
    
    # Create necessary groups first
    Group.objects.get_or_create(name='Shop Admins')
    print("✅ Created missing groups")
    
    # Import data in dependency order
    import_order = [
        ('userauths_data.json', 'Users'),
        ('categories_data.json', 'Categories'),
        ('brands_data.json', 'Brands'),
        ('shops_data.json', 'Shops'),
        ('products_data.json', 'Products'),
        ('addresses_data.json', 'Addresses'),
        ('orders_data.json', 'Orders'),
        ('order_items_data.json', 'Order Items'),
        ('wishlist_data.json', 'Wishlist'),
        ('reviews_data.json', 'Reviews'),
    ]
    
    successful_imports = 0
    
    for filename, description in import_order:
        try:
            print(f"Importing {description}...")
            call_command('loaddata', filename, verbosity=0)
            print(f"✅ {description} imported successfully")
            successful_imports += 1
        except Exception as e:
            print(f"❌ Error importing {description}: {e}")
            # Continue with other imports even if one fails
    
    print(f"\nImport completed: {successful_imports}/{len(import_order)} files imported successfully")

if __name__ == '__main__':
    import_data()