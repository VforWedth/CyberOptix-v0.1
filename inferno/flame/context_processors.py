from django.shortcuts import redirect, render, get_object_or_404
from flame.models import Product, Category,Brand, Shop, CartOrder, CartOrderItem, ProductImages, ProductReview , Wishlist, Address
from django.db.models import Min, Max

# Updated context processor
# Updated context processor
def default(request):
    context = {
        'product': Product.objects.all(),
        'categories': Category.objects.all(),
         # 'address': Address.objects.get(user=request.user),
        'brand': Brand.objects.all(),
        'shop': Shop.objects.all(),
        'min_max_price': Product.objects.aggregate(Min('price'), Max('price')),
        'shop_carts': [],
        'cart_total_amount': 0,
        'total_cart_items': 0,
        'wishlist_count': 0,
        'wishlist_products': [],
    }
    # Add wishlist count for authenticated users
    if request.user.is_authenticated:
        context['wishlist_count'] = Wishlist.objects.filter(user=request.user).count()


    if 'cart_data' in request.session:
        cart_data = request.session.get('cart_data', {})
        validated_carts = {}
        shop_carts = []
        
        # Use list comprehension for shop processing
        for shop_id, products in cart_data.items():
            try:
                shop = Shop.objects.get(shop_id=shop_id)
                shop_total = 0
                item_count = 0
                validated_products = {}

                # Process products with walrus operator (Python 3.8+)
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
                            validated_products[product_id] = validated_item
                            shop_total += validated_item['qty'] * validated_item['price']
                            item_count += 1
                        except (ValueError, TypeError) as e:
                            print(f"Invalid product {product_id} in shop {shop_id}: {e}")
                            continue

                if validated_products:  # Only add shops with valid products
                    shop_carts.append({
                        'shop': shop,
                        'products': validated_products,
                        'shop_total': round(shop_total, 2),
                        'item_count': item_count
                    })
                    
                    context['cart_total_amount'] = round(context['cart_total_amount'] + shop_total, 2)
                    context['total_cart_items'] += item_count

                validated_carts[shop_id] = validated_products

            except Shop.DoesNotExist:
                print(f"Shop {shop_id} not found - removing from cart")
                del cart_data[shop_id]  # Clean up invalid shops
                continue

        # Update session with validated data
        request.session['cart_data'] = {k: v for k, v in validated_carts.items() if v}
        context['shop_carts'] = sorted(
            shop_carts, 
            key=lambda x: x['shop'].title  # Sort shops alphabetically
        )

    # Add formatted currency strings for templates
    context.update({
        'formatted_cart_total': f"${context['cart_total_amount']:.2f}",
        'cart_total_rounded': round(context['cart_total_amount'], 2)
    })

    return context
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