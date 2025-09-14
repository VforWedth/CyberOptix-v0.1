# Generated for PostgreSQL optimization - corrected version
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0032_add_database_indexes'),
    ]

    operations = [
        # Basic indexes for commonly queried fields
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_category ON flame_product(category_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_category;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_brand ON flame_product(brand_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_brand;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_status ON flame_product(product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_price ON flame_product(price);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_price;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_date ON flame_product(date);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_user ON flame_cartorder(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_status ON flame_cartorder(product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_user ON flame_shop(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_slug ON flame_shop(slug);",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_slug;"
        ),
        
        # Composite indexes for common filter combinations
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_category_status ON flame_product(category_id, product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_category_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_brand_status ON flame_product(brand_id, product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_brand_status;"
        ),
    ]