from django.shortcuts import redirect, render, get_object_or_404
from flame.models import Product, Category,Brand, Shop, ExchangeRate,CartOrder, CartOrderItem, ProductImages, ProductReview , Wishlist, Address
from django.db.models import Min, Max
from django.utils import translation
from decimal import Decimal
from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency
# Updated context processor
def default(request):
    # Get current language
    current_language = translation.get_language()
    
    # Get exchange rate
    try:
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3500')  # Fallback rate
    
    context = {
        'product': Product.objects.all(),
        'categories': Category.objects.all(),
        'brand': Brand.objects.all(),
        'shop': Shop.objects.all(),
        'min_max_price': Product.objects.aggregate(Min('price'), Max('price')),
        'shop_carts': [],
        'cart_total_amount': 0,
        'total_cart_items': 0,
        'wishlist_count': 0,
        'wishlist_products': [],
        'current_language': current_language,
        'exchange_rate': exchange_rate,
        'is_myanmar': current_language == 'my',
    }
    
    # Add wishlist count for authenticated users
    if request.user.is_authenticated:
        context['wishlist_count'] = Wishlist.objects.filter(user=request.user).count()

    if 'cart_data' in request.session:
        cart_data = request.session.get('cart_data', {})
        validated_carts = {}
        shop_carts = []
        
        for shop_id, products in cart_data.items():
            try:
                shop = Shop.objects.get(shop_id=shop_id)
                shop_total = 0
                shop_quantity = 0
                validated_products = {}

                for product_id, item in products.items():
                    if all(key in item for key in ['title', 'qty', 'price', 'image', 'pid']):
                        try:
                            validated_item = {
                                'title': str(item['title']),
                                'qty': int(item['qty']),
                                'price': float(item['price']),
                                'image': str(item['image']),
                                'pid': str(item['pid']),
                                'sid': str(shop_id)
                            }
                            
                            # Calculate item total
                            item_total = validated_item['price'] * validated_item['qty']
                            
                            # Add formatted prices based on language
                            if current_language == 'my':
                                price_mmk = Decimal(str(item['price'])) * exchange_rate
                                validated_item['price_display'] = format_myanmar_currency(price_mmk)
                                item_total_mmk = price_mmk * int(item['qty'])
                                validated_item['total_display'] = format_myanmar_currency(item_total_mmk)
                            else:
                                validated_item['price_display'] = f"${validated_item['price']:.2f}"
                                validated_item['total_display'] = f"${item_total:.2f}"
                            
                            validated_products[product_id] = validated_item
                            shop_total += item_total
                            shop_quantity += validated_item['qty']
                        except (ValueError, TypeError) as e:
                            print(f"Invalid product {product_id} in shop {shop_id}: {e}")
                            continue

                if validated_products:
                    # Format shop total based on language
                    if current_language == 'my':
                        shop_total_mmk = Decimal(str(shop_total)) * exchange_rate
                        shop_total_display = format_myanmar_currency(shop_total_mmk)
                    else:
                        shop_total_display = f"${shop_total:.2f}"
                    
                    shop_carts.append({
                        'shop': shop,
                        'products': validated_products,
                        'total': shop_total,
                        'total_display': shop_total_display,
                        'shop_quantity': shop_quantity,
                        'item_count': len(validated_products)
                    })
                    
                    context['cart_total_amount'] += shop_total
                    context['total_cart_items'] += shop_quantity

                validated_carts[shop_id] = validated_products

            except Shop.DoesNotExist:
                print(f"Shop {shop_id} not found")
                continue

        request.session['cart_data'] = {k: v for k, v in validated_carts.items() if v}
        context['shop_carts'] = sorted(shop_carts, key=lambda x: x['shop'].title)

    # Format cart total based on language
    if current_language == 'my':
        cart_total_mmk = Decimal(str(context['cart_total_amount'])) * exchange_rate
        context['formatted_cart_total'] = format_myanmar_currency(cart_total_mmk)
        context['cart_total_display'] = format_myanmar_currency(cart_total_mmk)
    else:
        context['formatted_cart_total'] = f"${context['cart_total_amount']:.2f}"
        context['cart_total_display'] = f"${context['cart_total_amount']:.2f}"
    
    context['cart_total_rounded'] = round(context['cart_total_amount'], 2)
    context['totalcartitems'] = context['total_cart_items']  # Add this for template compatibility

    return context

def currency_context(request):
    """Additional context processor for currency data"""
    from django.utils import translation
    
    current_language = translation.get_language()
    
    try:
        from flame.models import ExchangeRate
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3500')
    
    return {
        'CURRENT_LANGUAGE': current_language,
        'EXCHANGE_RATE': exchange_rate,
        'IS_MYANMAR': current_language == 'my',
    }
# def default(request):
#     context = {
#         'product': Product.objects.all(),
#         'categories': Category.objects.all(),
#         # 'address': Address.objects.get(user=request.user),
#         'brand': Brand.objects.all(),
#         'shop': Shop.objects.all(),
#         'min_max_price': Product.objects.aggregate(Min('price'), Max('price')),
#         'cart_data': {},
#         'cart_total_amount': 0,
        
#     }

#     # Process cart data with type conversion
#     if 'cart_data_obj' in request.session:
#         cart_data = request.session['cart_data_obj']
#         validated_cart = {}
        
#         for item_id, item in cart_data.items():
#             try:
#                 # Convert values to proper types
#                 validated_cart[item_id] = {
#                     'title': str(item['title']),
#                     'qty': int(item['qty']),
#                     'price': float(item['price']),
#                     'image': str(item['image']),
#                     'pid': str(item['pid'])
#                 }
#                 context['cart_total_amount'] += validated_cart[item_id]['qty'] * validated_cart[item_id]['price']
#             except (ValueError, KeyError) as e:
#                 # Handle invalid entries
#                 print(f"Invalid cart item {item_id}: {e}")
#                 continue
        
#         context['cart_data'] = validated_cart
#         context['cart_items_count'] = len(validated_cart)
#         # Update session with validated data
#         request.session['cart_data_obj'] = validated_cart

#     return context

def shop_context(request):
    context = {}
    if 'shop_slug' in request.resolver_match.kwargs:
        shop_slug = request.resolver_match.kwargs['shop_slug']
        context['current_shop'] = get_object_or_404(Shop, slug=shop_slug)
    return context

# def currency_data(request):
#     active_rate = ExchangeRate.objects.filter(is_active=True).first()
#     return {
#         'exchange_rate': active_rate.usd_to_mmk if active_rate else 3500
#     }