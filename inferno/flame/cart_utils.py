from django.shortcuts import get_object_or_404
from .models import Shop, Product

def get_cart_data(request):
    """Safe cart data retrieval with initialization"""
    cart_data = request.session.get('cart_data', {
        'shops': {},
        'cart_total': 0.0
    })
    
    # Ensure proper structure
    cart_data.setdefault('shops', {})
    cart_data.setdefault('cart_total', 0.0)
    return cart_data

def update_cart_total(cart_data):
    """Recalculate cart total"""
    total = 0.0
    for shop_id, shop_data in cart_data['shops'].items():
        for product_id, product in shop_data['products'].items():
            total += float(product['price']) * int(product['qty'])
    cart_data['cart_total'] = round(total, 2)
    return cart_data

def save_cart(request, cart_data):
    """Save cart data to session with explicit modification"""
    request.session['cart_data'] = cart_data
    request.session.modified = True
    request.session.save()  # Force immediate save

def add_shop_to_cart(cart_data, shop):
    """Ensure shop entry exists in cart"""
    shop_id = str(shop.shop_id)
    if shop_id not in cart_data['shops']:
        cart_data['shops'][shop_id] = {
            'shop_info': {
                'title': shop.title,
                'image': shop.image.url if shop.image else '',
                'paypal_email': shop.paypal_email
            },
            'products': {}
        }
    return cart_data