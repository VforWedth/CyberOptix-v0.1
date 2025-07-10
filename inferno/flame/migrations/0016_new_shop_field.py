from django.db import migrations, models



class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0015_alter_product_shop'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='shop',
            field=models.CharField(max_length=100, null=True),
            
        ),
    ]
