from django.db import models
from django.utils import timezone
import hashlib
import uuid
import json


class MockPaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('TRADE_SUCCESS', 'Trade Success'),
        ('TRADE_FAILED', 'Trade Failed'),
        ('TRADE_CANCELED', 'Trade Canceled'),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    out_trade_no = models.CharField(max_length=100, unique=True)
    partner_id = models.CharField(max_length=50, default='2018082000010170')
    seller_id = models.CharField(max_length=50, default='2018082000010170')
    appid = models.CharField(max_length=50, default='2018082000010171')
    prepay_id = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MMK')
    subject = models.CharField(max_length=255)
    trade_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notify_url = models.URLField()
    qrcode = models.TextField()
    callback_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_time = models.DateTimeField(null=True, blank=True)

    # Additional fields for realistic experience
    merchant_name = models.CharField(max_length=255, default='LaptopMart Myanmar')
    merchant_logo = models.URLField(blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    order_items = models.JSONField(default=list, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    qr_code_data = models.TextField(blank=True)
    session_timeout = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.out_trade_no} - {self.trade_status}"

    def generate_qrcode(self):
        data = {
            'prepay_id': self.prepay_id,
            'partner_id': self.partner_id,
            'amount': str(self.total_amount),
            'currency': self.currency,
            'merchant_name': self.merchant_name,
            'order_id': self.out_trade_no,
            'timestamp': self.created_at.isoformat() if self.created_at else timezone.now().isoformat()
        }
        return json.dumps(data)

    def generate_mobile_qr_data(self):
        """Generate QR code data for mobile payment"""
        qr_data = f"kbzpay://pay?prepay_id={self.prepay_id}&amount={self.total_amount}&merchant={self.merchant_name}"
        self.qr_code_data = qr_data
        return qr_data

    def get_session_timeout_minutes(self):
        """Get session timeout in minutes"""
        if self.session_timeout:
            now = timezone.now()
            if self.session_timeout > now:
                diff = self.session_timeout - now
                return int(diff.total_seconds() / 60)
        return 0

    def is_session_expired(self):
        """Check if payment session has expired"""
        if self.session_timeout:
            return timezone.now() > self.session_timeout
        return False

    def mark_as_paid(self):
        self.trade_status = 'TRADE_SUCCESS'
        self.payment_time = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
