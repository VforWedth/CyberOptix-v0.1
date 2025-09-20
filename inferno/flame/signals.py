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
            # Extract shop_id, order_id, and address data from custom field
            # Format: "shop_id|order_id|address_encoded" or "shop_id|order_id" or just "shop_id" for backward compatibility
            custom_data = ipn_obj.custom
            if not custom_data:
                logger.error("No custom data found in PayPal IPN")
                return

            paypal_address_data = {}
            if '|' in custom_data:
                parts = custom_data.split('|')
                shop_id = parts[0]
                paypal_order_id = parts[1] if len(parts) > 1 else ipn_obj.invoice

                # Try to decode address data
                if len(parts) > 2:
                    try:
                        import base64
                        import json
                        address_encoded = parts[2]
                        address_json = base64.b64decode(address_encoded.encode()).decode()
                        paypal_address_data = json.loads(address_json)
                        logger.info(f"PayPal address data decoded successfully: {paypal_address_data}")
                    except Exception as e:
                        # Fallback: treat third part as mobile for backward compatibility
                        paypal_address_data = {'mobile': parts[2]}
                        logger.warning(f"Could not decode address data, treating as mobile: {e}")
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

            # Build delivery address and phone from PayPal address data
            delivery_address = ""
            delivery_phone = ""

            # First priority: Use PayPal checkout address data if available
            if paypal_address_data:
                try:
                    from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

                    # Get address components from PayPal data
                    state_id = paypal_address_data.get('state')
                    city_id = paypal_address_data.get('city')
                    township_id = paypal_address_data.get('township')
                    street_address = paypal_address_data.get('street_address', '')
                    landmark = paypal_address_data.get('landmark', '')

                    # Get mobile from PayPal data
                    delivery_phone = paypal_address_data.get('mobile', '').strip() or "Not provided"

                    # Build address from location IDs
                    address_parts = []
                    if street_address:
                        address_parts.append(street_address)

                    if township_id:
                        try:
                            township = MyanmarTownship.objects.get(id=township_id)
                            address_parts.append(township.name)
                        except MyanmarTownship.DoesNotExist:
                            pass

                    if city_id:
                        try:
                            city = MyanmarCity.objects.get(id=city_id)
                            address_parts.append(city.name)
                        except MyanmarCity.DoesNotExist:
                            pass

                    if state_id:
                        try:
                            state = MyanmarState.objects.get(id=state_id)
                            address_parts.append(state.name)
                        except MyanmarState.DoesNotExist:
                            pass

                    if landmark:
                        address_parts.append(f"Near {landmark}")

                    delivery_address = ", ".join(address_parts) if address_parts else "PayPal checkout address"
                    logger.info(f"Built address from PayPal data: {delivery_address}")

                except Exception as e:
                    logger.error(f"Error building address from PayPal data: {e}")
                    # Fallback to stored address
                    paypal_address_data = {}

            # Fallback: Use user's stored address if PayPal address data not available
            if not delivery_address:
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
                    # Use stored address mobile if not already set from PayPal
                    if not delivery_phone or delivery_phone == "Not provided":
                        delivery_phone = active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else "Not provided"

                except Address.DoesNotExist:
                    delivery_address = f"PayPal Address: {ipn_obj.address_street}, {ipn_obj.address_city}, {ipn_obj.address_state} {ipn_obj.address_zip}, {ipn_obj.address_country}"
                    if not delivery_phone or delivery_phone == "Not provided":
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

            # Create order item representing the PayPal purchase
            # Since PayPal processes orders asynchronously, we create a consolidated order item
            CartOrderItem.objects.create(
                order=order,
                item=f"Order from {shop.title} (PayPal)",
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