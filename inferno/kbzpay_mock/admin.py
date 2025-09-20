from django.contrib import admin
from .models import MockPaymentTransaction


@admin.register(MockPaymentTransaction)
class MockPaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['out_trade_no', 'prepay_id', 'total_amount', 'currency', 'trade_status', 'created_at', 'payment_time']
    list_filter = ['trade_status', 'currency', 'created_at', 'callback_sent']
    search_fields = ['out_trade_no', 'prepay_id', 'transaction_id']
    readonly_fields = ['transaction_id', 'prepay_id', 'qrcode', 'created_at', 'updated_at']

    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'out_trade_no', 'prepay_id', 'subject')
        }),
        ('Payment Details', {
            'fields': ('total_amount', 'currency', 'trade_status', 'payment_time')
        }),
        ('Merchant Info', {
            'fields': ('partner_id', 'seller_id', 'appid')
        }),
        ('Callback', {
            'fields': ('notify_url', 'callback_sent', 'qrcode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
