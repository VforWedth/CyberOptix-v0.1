# Generated for PostgreSQL optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0031_add_order_number_unique_constraint'),
    ]

    operations = [
        # Product indexes for better search and filtering performance
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
            "CREATE INDEX IF NOT EXISTS idx_product_in_stock ON flame_product(in_stock);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_in_stock;"
        ),
        
        # Order indexes for better performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_user ON flame_cartorder(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_status ON flame_cartorder(product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_date ON flame_cartorder(order_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_cartorder_number ON flame_cartorder(order_number);",
            reverse_sql="DROP INDEX IF EXISTS idx_cartorder_number;"
        ),
        
        # User authentication indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_email ON userauths_user(email);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_email;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_username ON userauths_user(username);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_username;"
        ),
        
        # Review indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_review_product ON flame_productreview(product_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_review_product;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_review_user ON flame_productreview(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_review_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_review_date ON flame_productreview(date);",
            reverse_sql="DROP INDEX IF EXISTS idx_review_date;"
        ),
        
        # Wishlist indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_wishlist_user ON flame_wishlist(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_wishlist_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_wishlist_product ON flame_wishlist(product_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_wishlist_product;"
        ),
        
        # Address indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_address_user ON flame_address(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_address_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_address_status ON flame_address(status);",
            reverse_sql="DROP INDEX IF EXISTS idx_address_status;"
        ),
        
        # Shop indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_user ON flame_shop(user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_slug ON flame_shop(slug);",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_slug;"
        ),
        
        # Composite indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_category_status ON flame_product(category_id, product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_category_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_brand_status ON flame_product(brand_id, product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_brand_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_product_price_status ON flame_product(price, product_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_product_price_status;"
        ),
    ]