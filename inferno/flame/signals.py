# flame/signals.py
from django.dispatch import receiver
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received
from django.contrib.auth.models import User
from flame.models import CartOrder, CartOrderItem, Shop
from django.utils import translation
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    """
    Handle successful PayPal payment notifications
    """
    ipn_obj = sender
    logger.info(f"PayPal IPN received: {ipn_obj.payment_status} for {ipn_obj.invoice}")

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        try:
            # Extract shop_id and order_id from custom field
            # Format: "shop_id|order_id" or just "shop_id" for backward compatibility
            custom_data = ipn_obj.custom
            if not custom_data:
                logger.error("No custom data found in PayPal IPN")
                return

            if '|' in custom_data:
                shop_id, paypal_order_id = custom_data.split('|', 1)
            else:
                shop_id = custom_data
                paypal_order_id = ipn_obj.invoice

            # Get user by email
            try:
                user = User.objects.get(email=ipn_obj.payer_email)
            except User.DoesNotExist:
                logger.error(f"User not found for email: {ipn_obj.payer_email}")
                return

            # Get shop
            try:
                shop = Shop.objects.get(shop_id=shop_id)
            except Shop.DoesNotExist:
                logger.error(f"Shop not found: {shop_id}")
                return

            # Check if order already exists
            existing_order = CartOrder.objects.filter(
                user=user,
                shop=shop,
                paypal_payment_intent=ipn_obj.txn_id
            ).first()

            if existing_order:
                logger.info(f"Order already exists for PayPal transaction: {ipn_obj.txn_id}")
                return

            # Get cart data and address from user's session
            # Note: Since this is an async signal, we need to get address from user's active address
            from flame.models import Address
            try:
                active_address = Address.objects.get(user=user, status=True)
                delivery_parts = []

                if active_address.street_address:
                    delivery_parts.append(active_address.street_address)
                if active_address.township:
                    delivery_parts.append(active_address.township.name)
                if active_address.city:
                    delivery_parts.append(active_address.city.name)
                if active_address.state:
                    delivery_parts.append(active_address.state.name)
                if active_address.landmark:
                    delivery_parts.append(f"Near {active_address.landmark}")

                delivery_address = ", ".join(delivery_parts)
                delivery_phone = active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else "Not provided"

            except Address.DoesNotExist:
                delivery_address = f"PayPal Address: {ipn_obj.address_street}, {ipn_obj.address_city}, {ipn_obj.address_state} {ipn_obj.address_zip}, {ipn_obj.address_country}"
                delivery_phone = "Not provided"

            # Calculate amounts
            gross_amount = Decimal(str(ipn_obj.mc_gross))
            shipping_cost = Decimal(str(ipn_obj.mc_shipping or 0))
            subtotal = gross_amount - shipping_cost

            # Create order
            order = CartOrder.objects.create(
                user=user,
                shop=shop,
                price=subtotal,
                shipping_cost=shipping_cost,
                total_amount=gross_amount,
                order_type='shop',
                payment_method='paypal',
                paid_status=True,
                delivery_address=delivery_address,
                delivery_phone=delivery_phone,
                paypal_payment_intent=ipn_obj.txn_id
            )

            # Create order items from PayPal item details
            # Note: For proper implementation, we should store cart data in a more persistent way
            # For now, we'll create a single item representing the total purchase
            CartOrderItem.objects.create(
                order=order,
                item=f"PayPal Purchase from {shop.title}",
                image="",  # Default image or shop logo
                qty=1,
                price=subtotal,
                total=subtotal
            )

            logger.info(f"PayPal order created successfully: Order #{order.id}")

            # Send notification email (optional)
            from flame.services.notification_service import NotificationService
            try:
                NotificationService.send_order_confirmation_email(order)
            except Exception as e:
                logger.warning(f"Failed to send order confirmation email: {e}")

        except Exception as e:
            logger.error(f"Error processing PayPal payment: {e}", exc_info=True)
    else:
        logger.warning(f"PayPal payment not completed. Status: {ipn_obj.payment_status}")

@receiver(invalid_ipn_received)
def paypal_payment_invalid(sender, **kwargs):
    """
    Handle invalid PayPal IPN notifications
    """
    ipn_obj = sender
    logger.warning(f"Invalid PayPal IPN received: {ipn_obj.payment_status} for {ipn_obj.invoice}")