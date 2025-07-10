from django.db import migrations
from django.utils.text import slugify

def generate_unique_slugs(apps, schema_editor):
    Shop = apps.get_model('flame', 'Shop')
    for shop in Shop.objects.all():
        base_slug = slugify(shop.title)
        unique_slug = base_slug
        counter = 1
        while Shop.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        shop.slug = unique_slug
        shop.save()

class Migration(migrations.Migration):
    dependencies = [
        ('flame', '0009_remove_cartorder_shop_remove_shop_paypal_email_and_more'),
    ]

    operations = [
        migrations.RunPython(generate_unique_slugs),
    ]