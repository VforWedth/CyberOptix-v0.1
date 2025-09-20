# PayPal Dynamic Payment Handler
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from decimal import Decimal
import json
import time

from flame.models import Shop, MyanmarState, MyanmarCity, MyanmarTownship

@login_required
def create_paypal_payment_with_shipping(request, sid):
    """Create PayPal payment form with dynamic shipping"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Get shop
        shop = Shop.objects.get(shop_id=sid)

        # Get cart data for this shop
        cart_data = request.session.get('cart_data', {}).get(sid, {})
        if not cart_data:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # Calculate base order total
        order_total = sum(
            int(item.get('qty', 0)) * float(item.get('price', 0))
            for item in cart_data.values()
        )

        # Get address and shipping data from request
        data = json.loads(request.body)
        state_id = data.get('state')
        city_id = data.get('city')
        township_id = data.get('township')
        street_address = data.get('street_address', '')
        landmark = data.get('landmark', '')
        mobile = data.get('mobile', '')
        shipping_fee = float(data.get('shipping_fee', 0))

        if not all([state_id, city_id]):
            return JsonResponse({'error': 'State and city are required'}, status=400)

        # Store address data in session for later use
        address_data = {
            'state': str(state_id),
            'city': str(city_id),
            'township': str(township_id) if township_id else '',
            'street_address': street_address.strip(),
            'landmark': landmark.strip(),
            'mobile': mobile.strip(),
            'shipping_fee': shipping_fee,
            'timestamp': int(time.time()),  # Add timestamp for session validation
            'shop_id': sid  # Add shop_id for validation
        }

        # Store with backup - both specific and general session keys
        request.session['checkout_address_data'] = address_data
        request.session[f'checkout_address_{sid}'] = address_data  # Shop-specific backup
        request.session.modified = True

        # Set session to expire in 2 hours for checkout data
        if not request.session.get_expiry_age():
            request.session.set_expiry(7200)  # 2 hours

        # Calculate total with shipping
        total_with_shipping = order_total + shipping_fee

        # Create PayPal order ID for tracking
        import uuid
        order_id = f"PP{uuid.uuid4().hex[:8].upper()}"

        # PayPal configuration with shipping
        paypal_dict = {
            'business': shop.paypal_email if shop.paypal_email else settings.PAYPAL_RECEIVER_EMAIL,
            'amount': f"{total_with_shipping:.2f}",
            'shipping': f"{shipping_fee:.2f}",
            'item_name': f"Order from {shop.title}",
            'invoice': order_id,
            'currency_code': "USD",
            'notify_url': request.build_absolute_uri(reverse("flame:paypal-ipn")),
            'return_url': request.build_absolute_uri(reverse("flame:payment-completed", args=[sid])),
            'cancel_url': request.build_absolute_uri(reverse("flame:payment-failed")),
            'custom': f"{sid}|{order_id}",  # Pass shop_id and order_id for signal handler
        }

        # Validate PayPal configuration
        if not paypal_dict['business']:
            return JsonResponse({'error': 'PayPal configuration error: No business email configured'}, status=500)

        # Create PayPal form
        try:
            paypal_form = PayPalPaymentsForm(initial=paypal_dict)
            form_html = paypal_form.render()
        except Exception as e:
            return JsonResponse({'error': f'PayPal form creation failed: {str(e)}'}, status=500)

        # Validate form HTML was generated
        if not form_html or len(form_html.strip()) < 50:
            return JsonResponse({'error': 'PayPal form generation failed'}, status=500)

        return JsonResponse({
            'success': True,
            'form_html': form_html,
            'total_amount': total_with_shipping,
            'shipping_fee': shipping_fee,
            'subtotal': order_total,
            'mobile': mobile,
            'order_id': order_id
        })

    except Shop.DoesNotExist:
        return JsonResponse({'error': 'Shop not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data format'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid data value: {str(e)}'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PayPal payment creation error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Payment processing error. Please try again.'}, status=500)