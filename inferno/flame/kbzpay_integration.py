from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from flame.models import CartOrder
import json
import hashlib
import requests
import uuid


def generate_kbzpay_signature(params, api_key='6ab2757c99c54f9c882dbb819d2fe8e1'):
    """Generate MD5 signature for KBZPay API"""
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params if v and k != 'sign'])
    sign_string = param_string + api_key
    return hashlib.md5(sign_string.encode()).hexdigest()


@login_required
def initiate_kbzpay_payment(request, order_id):
    """Initiate KBZPay payment for an order"""
    try:
        order = CartOrder.objects.get(id=order_id, user=request.user)

        # Get order items for detailed transaction
        order_items = []
        for item in order.cartorderitem_set.all():
            order_items.append({
                'name': str(item.item),
                'quantity': item.qty,
                'price': float(item.price),
                'total': float(item.total())
            })

        # Get address data from session and update order if needed
        address_data = request.session.get('checkout_address_data', {})

        # Build delivery address if available and not already set
        if address_data and not order.delivery_address:
            try:
                from flame.models import MyanmarState, MyanmarCity, MyanmarTownship
                state = MyanmarState.objects.get(id=address_data.get('state')) if address_data.get('state') else None
                city = MyanmarCity.objects.get(id=address_data.get('city')) if address_data.get('city') else None
                township = MyanmarTownship.objects.get(id=address_data.get('township')) if address_data.get('township') else None

                parts = []
                if address_data.get('street_address'):
                    parts.append(address_data.get('street_address'))
                if township:
                    parts.append(township.name)
                if city:
                    parts.append(city.name)
                if state:
                    parts.append(state.name)
                if address_data.get('landmark'):
                    parts.append(f"Near {address_data.get('landmark')}")

                delivery_address = ", ".join(parts)

                # Update order with delivery address, phone, and shipping fee
                order.delivery_address = delivery_address
                if address_data.get('mobile'):
                    order.delivery_phone = address_data.get('mobile')
                if address_data.get('shipping_fee'):
                    order.shipping_cost = float(address_data.get('shipping_fee'))
                    order.total_amount = order.price + order.shipping_cost
                order.save()

            except Exception as e:
                print(f"Error updating order address: {e}")
                # Continue with payment even if address update fails

        # Prepare comprehensive order data
        order_data = {
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
            'order_items': order_items,
            'shipping_address': {
                'state': getattr(order.state, 'name', '') if hasattr(order, 'state') and order.state else '',
                'city': getattr(order.city, 'name', '') if hasattr(order, 'city') and order.city else '',
                'address': order.delivery_address or ''
            }
        }

        # Prepare KBZPay precreate parameters
        params = {
            'partner_id': '2018082000010170',  # Mock credentials
            'seller_id': '2018082000010170',
            'appid': '2018082000010171',
            'out_trade_no': str(order.oid),
            'total_amount': str(order.price),
            'currency': 'MMK',
            'subject': f'LaptopMart Order #{order.oid}',
            'notify_url': request.build_absolute_uri('/payment/kbzpay/callback/'),
            'order_data': json.dumps(order_data)  # Pass order data
        }

        # Add signature
        params['sign'] = generate_kbzpay_signature(params)

        # Call mock KBZPay precreate API
        api_url = request.build_absolute_uri('/kbzpay/api/precreate/')

        response = requests.post(api_url, json=params)
        response_data = response.json()

        if response_data.get('code') == 'SUCCESS':
            # Store prepay_id in session for later verification
            request.session[f'kbzpay_prepay_{order.oid}'] = response_data['data']['prepay_id']

            return JsonResponse({
                'success': True,
                'prepay_id': response_data['data']['prepay_id'],
                'qrcode': response_data['data']['qrcode'],
                'payment_url': request.build_absolute_uri(f"/kbzpay/payment/{response_data['data']['prepay_id']}/"),
                'order_data': order_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': response_data.get('msg', 'Failed to initialize payment')
            })

    except CartOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
def kbzpay_callback(request):
    """Handle KBZPay payment callback"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    try:
        # Get callback data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        # Verify signature
        received_sign = data.pop('sign', '')
        calculated_sign = generate_kbzpay_signature(data)

        if received_sign != calculated_sign:
            return HttpResponse('Invalid signature', status=400)

        # Process payment result
        out_trade_no = data.get('out_trade_no')
        trade_status = data.get('trade_status')

        if trade_status == 'TRADE_SUCCESS':
            # Update order status
            try:
                order = CartOrder.objects.get(oid=out_trade_no)
                order.paid_status = True
                order.payment_method = 'KBZPay'
                order.save()

                # You can add additional logic here like sending confirmation emails

                return HttpResponse('SUCCESS')
            except CartOrder.DoesNotExist:
                return HttpResponse('Order not found', status=404)

        return HttpResponse('SUCCESS')  # Always return SUCCESS to stop retries

    except Exception as e:
        return HttpResponse(str(e), status=500)


@login_required
def check_payment_status(request, order_id):
    """Check KBZPay payment status for an order"""
    try:
        order = CartOrder.objects.get(id=order_id, user=request.user)

        # Get prepay_id from session
        prepay_id = request.session.get(f'kbzpay_prepay_{order.oid}')

        if not prepay_id:
            return JsonResponse({
                'success': False,
                'message': 'Payment session not found'
            })

        # Query payment status from KBZPay
        api_url = request.build_absolute_uri('/kbzpay/api/query/')
        response = requests.post(api_url, json={
            'out_trade_no': str(order.oid),
            'prepay_id': prepay_id
        })

        response_data = response.json()

        if response_data.get('code') == 'SUCCESS':
            trade_status = response_data['data'].get('trade_status')

            if trade_status == 'TRADE_SUCCESS':
                # Update order if not already updated
                if not order.paid_status:
                    order.paid_status = True
                    order.payment_method = 'KBZPay'
                    order.save()

            return JsonResponse({
                'success': True,
                'status': trade_status,
                'paid': trade_status == 'TRADE_SUCCESS'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': response_data.get('msg', 'Failed to query status')
            })

    except CartOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)