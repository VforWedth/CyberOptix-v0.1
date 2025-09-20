# KBZPay Mock Payment Integration

## Overview
This is a fully functional mock implementation of KBZPay payment gateway for educational and testing purposes. It simulates the complete KBZPay payment flow without requiring real credentials or processing actual payments.

## Features
- ✅ Complete payment flow simulation
- ✅ Mock API endpoints matching KBZPay's real API structure
- ✅ Payment confirmation page
- ✅ JavaScript SDK for frontend integration
- ✅ Callback/webhook simulation
- ✅ Admin interface for monitoring transactions
- ✅ Support for Myanmar Kyat (MMK) currency

## Components

### 1. Backend Components
- **Django App**: `kbzpay_mock` - Contains all mock payment logic
- **Models**: `MockPaymentTransaction` - Stores payment transactions
- **API Endpoints**:
  - `/kbzpay/api/precreate/` - Create payment session
  - `/kbzpay/api/query/` - Query payment status
  - `/kbzpay/payment/<prepay_id>/` - Payment confirmation page
  - `/kbzpay/simulate/success/<prepay_id>/` - Simulate successful payment (for testing)

### 2. Frontend Components
- **JavaScript SDK**: `/static/js/kbzpay-mock.js`
- **Templates**: Payment confirmation, success, and cancellation pages
- **Integration**: Checkout page with KBZPay button

## How It Works

### Payment Flow
1. **Initialize Payment**: User clicks "Pay with KBZPay" on checkout page
2. **Create Session**: Backend calls precreate API to create payment session
3. **Open Payment Window**: JavaScript SDK opens payment confirmation popup
4. **User Action**: User confirms or cancels payment in popup
5. **Process Result**: Backend processes payment and sends callback
6. **Update Order**: Order status is updated based on payment result

### Mock Credentials (for testing)
```python
partner_id = '2018082000010170'
seller_id = '2018082000010170'
appid = '2018082000010171'
api_key = '6ab2757c99c54f9c882dbb819d2fe8e1'
```

## Testing

### Run Test Script
```bash
cd inferno
python test_kbzpay_mock.py
```

### Manual Testing
1. Start Django server: `python manage.py runserver`
2. Navigate to checkout page with items in cart
3. Click "Pay with KBZPay" button
4. Confirm payment in popup window
5. Check order status in admin panel

### Admin Panel
Access KBZPay transactions in Django admin:
- URL: `/admin/kbzpay_mock/mockpaymenttransaction/`
- View all payment transactions
- Monitor payment status
- Check callback status

## Integration Guide

### 1. Frontend Integration
Include the KBZPay mock JS SDK in your template:
```html
<script src="{% static 'js/kbzpay-mock.js' %}"></script>
```

### 2. Initialize Payment
```javascript
// When user clicks pay button
fetch('/kbzpay/initiate/<order_id>/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Open payment window
        KBZPayJS.pay(data.qrcode, function(result) {
            if (result.code === 0) {
                // Payment successful
                console.log('Payment successful!');
            }
        });
    }
});
```

### 3. Handle Callback
The system automatically handles callbacks at `/kbzpay/callback/` endpoint.

## API Documentation

### Precreate API
**Endpoint**: `POST /kbzpay/api/precreate/`

**Request Body**:
```json
{
    "partner_id": "2018082000010170",
    "seller_id": "2018082000010170",
    "out_trade_no": "ORDER_123456",
    "total_amount": "50000",
    "currency": "MMK",
    "subject": "Order Description",
    "notify_url": "http://yoursite.com/callback/",
    "sign": "md5_signature"
}
```

**Response**:
```json
{
    "code": "SUCCESS",
    "msg": "Success",
    "data": {
        "prepay_id": "kbz_abc123",
        "qrcode": "{json_data}",
        "out_trade_no": "ORDER_123456"
    }
}
```

### Query Status API
**Endpoint**: `POST /kbzpay/api/query/`

**Request Body**:
```json
{
    "prepay_id": "kbz_abc123"
}
```

**Response**:
```json
{
    "code": "SUCCESS",
    "msg": "Success",
    "data": {
        "out_trade_no": "ORDER_123456",
        "prepay_id": "kbz_abc123",
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "50000",
        "currency": "MMK",
        "payment_time": "2024-01-15T10:30:00"
    }
}
```

## Security Notes
⚠️ **IMPORTANT**: This is a MOCK implementation for educational purposes only!
- Do NOT use in production environments
- No real payments are processed
- Mock credentials are hardcoded for testing
- Always use official KBZPay SDK for production

## Troubleshooting

### Common Issues
1. **Payment window not opening**: Check if popup blocker is enabled
2. **Callback not received**: Ensure notify_url is accessible
3. **Signature verification failed**: Check API key and parameter ordering

### Debug Mode
Enable debug logging in views to troubleshoot issues:
```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

## Future Enhancements
- [ ] Add QR code generation for mobile payments
- [ ] Implement refund simulation
- [ ] Add payment expiration
- [ ] Support multiple currencies
- [ ] Add more detailed transaction logs
- [ ] Implement rate limiting

## License
This mock implementation is for educational purposes only. KBZPay is a trademark of KBZ Bank.

## Support
For issues or questions about this mock implementation, please refer to the project documentation or create an issue in the repository.