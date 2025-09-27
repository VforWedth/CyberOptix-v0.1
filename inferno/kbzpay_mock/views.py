from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import MockPaymentTransaction
import json
import hashlib
import uuid
import requests
import time


def generate_signature(params, api_key='6ab2757c99c54f9c882dbb819d2fe8e1'):
    """Generate MD5 signature for KBZPay mock API"""
    sorted_params = sorted(params.items())
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params if v and k != 'sign'])
    sign_string = param_string + api_key
    return hashlib.md5(sign_string.encode()).hexdigest()


@csrf_exempt
@require_http_methods(["POST"])
def mock_precreate(request):
    """Mock KBZPay precreate API endpoint"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        required_fields = ['partner_id', 'seller_id', 'out_trade_no', 'total_amount', 'subject', 'notify_url']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'code': 'PARAM_ERROR',
                    'msg': f'Missing required field: {field}',
                    'data': {}
                }, status=400)

        prepay_id = f"kbz_{uuid.uuid4().hex[:16]}"

        # Parse order data if provided
        order_data = {}
        if 'order_data' in data:
            try:
                order_data = json.loads(data['order_data']) if isinstance(data['order_data'], str) else data['order_data']
            except (json.JSONDecodeError, TypeError):
                order_data = {}

        # Set session timeout (15 minutes from now)
        session_timeout = timezone.now() + timezone.timedelta(minutes=15)

        transaction = MockPaymentTransaction.objects.create(
            out_trade_no=data['out_trade_no'],
            partner_id=data.get('partner_id', '2018082000010170'),
            seller_id=data.get('seller_id', '2018082000010170'),
            appid=data.get('appid', '2018082000010171'),
            prepay_id=prepay_id,
            total_amount=data['total_amount'],
            currency=data.get('currency', 'MMK'),
            subject=data['subject'],
            notify_url=data['notify_url'],
            qrcode="",
            # Enhanced fields
            customer_name=order_data.get('customer_name', ''),
            customer_email=order_data.get('customer_email', ''),
            order_items=order_data.get('order_items', []),
            shipping_address=order_data.get('shipping_address', {}),
            session_timeout=session_timeout
        )

        transaction.qrcode = transaction.generate_qrcode()
        transaction.qr_code_data = transaction.generate_mobile_qr_data()
        transaction.save()

        response_data = {
            'code': 'SUCCESS',
            'msg': 'Success',
            'data': {
                'prepay_id': prepay_id,
                'qrcode': transaction.qrcode,
                'qr_code_data': transaction.qr_code_data,
                'out_trade_no': data['out_trade_no'],
                'payment_url': f'/kbzpay/payment/{prepay_id}/',
                'session_timeout': transaction.session_timeout.isoformat() if transaction.session_timeout else None
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'code': 'SYSTEM_ERROR',
            'msg': str(e),
            'data': {}
        }, status=500)


@csrf_exempt
def mock_payment_page(request, prepay_id):
    """Mock KBZPay payment confirmation page"""
    try:
        transaction = MockPaymentTransaction.objects.get(prepay_id=prepay_id)

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'confirm':
                transaction.mark_as_paid()

                # Send callback to merchant notify_url
                callback_data = {
                    'partner_id': transaction.partner_id,
                    'seller_id': transaction.seller_id,
                    'out_trade_no': transaction.out_trade_no,
                    'trade_status': 'TRADE_SUCCESS',
                    'total_amount': str(transaction.total_amount),
                    'currency': transaction.currency,
                    'prepay_id': transaction.prepay_id,
                    'payment_time': transaction.payment_time.isoformat() if transaction.payment_time else None
                }
                callback_data['sign'] = generate_signature(callback_data)

                try:
                    # Try to send callback notification
                    response = requests.post(transaction.notify_url, data=callback_data, timeout=5)
                    if response.text.strip().upper() == 'SUCCESS':
                        transaction.callback_sent = True
                        transaction.save()
                except:
                    pass  # In mock mode, we continue even if callback fails

                return render(request, 'kbzpay_mock/payment_success.html', {
                    'transaction': transaction
                })

            elif action == 'cancel':
                transaction.trade_status = 'TRADE_CANCELED'
                transaction.save()
                return render(request, 'kbzpay_mock/payment_canceled.html', {
                    'transaction': transaction
                })

        return render(request, 'kbzpay_mock/payment_confirm.html', {
            'transaction': transaction
        })

    except MockPaymentTransaction.DoesNotExist:
        return HttpResponse("Transaction not found", status=404)


@csrf_exempt
@require_http_methods(["POST"])
def mock_query_status(request):
    """Mock API to query payment status"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()

        out_trade_no = data.get('out_trade_no')
        prepay_id = data.get('prepay_id')

        if not out_trade_no and not prepay_id:
            return JsonResponse({
                'code': 'PARAM_ERROR',
                'msg': 'Either out_trade_no or prepay_id is required',
                'data': {}
            }, status=400)

        if out_trade_no:
            transaction = MockPaymentTransaction.objects.get(out_trade_no=out_trade_no)
        else:
            transaction = MockPaymentTransaction.objects.get(prepay_id=prepay_id)

        return JsonResponse({
            'code': 'SUCCESS',
            'msg': 'Success',
            'data': {
                'out_trade_no': transaction.out_trade_no,
                'prepay_id': transaction.prepay_id,
                'trade_status': transaction.trade_status,
                'total_amount': str(transaction.total_amount),
                'currency': transaction.currency,
                'payment_time': transaction.payment_time.isoformat() if transaction.payment_time else None
            }
        })

    except MockPaymentTransaction.DoesNotExist:
        return JsonResponse({
            'code': 'TRADE_NOT_EXIST',
            'msg': 'Trade does not exist',
            'data': {}
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'code': 'SYSTEM_ERROR',
            'msg': str(e),
            'data': {}
        }, status=500)


def simulate_payment_success(request, prepay_id):
    """Automatically simulate successful payment (for testing)"""
    try:
        transaction = MockPaymentTransaction.objects.get(prepay_id=prepay_id)
        transaction.mark_as_paid()

        # Send callback
        callback_data = {
            'partner_id': transaction.partner_id,
            'seller_id': transaction.seller_id,
            'out_trade_no': transaction.out_trade_no,
            'trade_status': 'TRADE_SUCCESS',
            'total_amount': str(transaction.total_amount),
            'currency': transaction.currency,
            'prepay_id': transaction.prepay_id,
            'payment_time': transaction.payment_time.isoformat() if transaction.payment_time else None
        }
        callback_data['sign'] = generate_signature(callback_data)

        try:
            response = requests.post(transaction.notify_url, data=callback_data, timeout=5)
            if response.text.strip().upper() == 'SUCCESS':
                transaction.callback_sent = True
                transaction.save()
        except:
            pass

        return JsonResponse({
            'code': 'SUCCESS',
            'msg': 'Payment simulated successfully',
            'data': {
                'prepay_id': prepay_id,
                'trade_status': 'TRADE_SUCCESS'
            }
        })

    except MockPaymentTransaction.DoesNotExist:
        return JsonResponse({
            'code': 'TRADE_NOT_EXIST',
            'msg': 'Trade does not exist',
            'data': {}
        }, status=404)
