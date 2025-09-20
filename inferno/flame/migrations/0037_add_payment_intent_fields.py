# Generated migration for payment intent fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0036_checkoutsession'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartorder',
            name='stripe_payment_intent',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='cartorder',
            name='paypal_payment_intent',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]