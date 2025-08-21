from django.shortcuts import redirect, render, get_object_or_404
from django.utils.dateformat import format as date_format
from django.utils import timezone
from django.http import HttpResponse,JsonResponse, HttpResponseBadRequest
from flame.models import Brand, Product,ExchangeRate, Category, Shop, CartOrder, CartOrderItem, ProductImages, ProductReview , Wishlist, Address

from django.db.models import Count,Avg,F, ExpressionWrapper, FloatField
from flame.forms import ProductReviewForm
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import get_language, activate
from django.views.i18n import set_language
from flame.utils.myanmar_utils import format_price_display, format_myanmar_currency, format_usd_currency
from django.utils import translation
from decimal import Decimal

#for payment integration process 
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from paypal.standard.forms import  PayPalPaymentsForm
import uuid, requests
from inferno.pgw import sign_pgw_payload
import hmac, hashlib, json

from django.core import serializers
import stripe
import barcode
from barcode.writer import ImageWriter
from django.core.files.base import ContentFile

def home(request):
     # Get current language
    current_language = translation.get_language()
    
    shop_views=Shop.objects.all()
 
    items = Product.objects.filter(shop__isnull=False, product_status="published")
    # Base filter: only published products that belong to a shop
    base_qs = Product.objects.filter(
        shop__isnull=False,
        product_status="published",
        status=True,
        in_stock=True
    )

    # 1) Most Popular: rank by number of reviews (you could swap in sales or pageviews if you track them)
        # Use translated fields in ordering
    if current_language == 'my':
        popular_qs = base_qs.annotate(
            review_count=Count('productreview')
        ).order_by('-review_count', '-date')[:10]
    else:
        popular_qs = base_qs.annotate(
            review_count=Count('productreview')
        ).order_by('-review_count', '-date')[:10]
        
    # 2) Discounted Items: where price < old_price
    #    and sort by percentage saved
    discount_expr = ExpressionWrapper(
        (F('old_price') - F('price')) / F('old_price') * 100,
        output_field=FloatField()
    )
    discounted_qs = (
        base_qs
        .filter(old_price__gt=F('price'))
        .annotate(discount_pct=discount_expr)
        .order_by('-discount_pct')[:10]         # discount_pct = ((old_price – price) / old_price) * 100
    )

    # 3) Newest Arrivals: simply the most recently created
    new_qs = base_qs.order_by('-date')[:10]

    return render(request, 'flame/home.html', {
        'items': items,
        'popular_items': popular_qs,
        'discounted_items': discounted_qs,
        'new_items': new_qs,
        'shop_views':shop_views,
        'current_language': current_language,
        'page_title': _('Welcome to CyberOptix'),  # Translatable string
    })
    
# Add language switcher view
def switch_language(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        if language and language in ['en', 'my']:
            activate(language)
            request.session['django_language'] = language
            
            # Get the next URL or default to home
            next_url = request.POST.get('next', '/')
            return redirect(next_url)
    
    return redirect('/')

CATEGORY_MAP = {
    "Desktop": _("ဒက်စ်တော့"),
    "Laptop": _("လက်ပ်တော့"),
    "Accessories": _("အသုံး အဆောင်ပစ္စည်းများ"),
}
# Product List View
def product_list_view(request):
    shop_views = Shop.objects.all()
    brand = request.GET.get('brand', '')
    category = request.GET.get('category', '')
    item_type = request.GET.get('items', '')  # Get the item type filter
    
    # Base queryset
    base_qs = Product.objects.filter(
        shop__isnull=False,
        product_status="published",
        status=True,
        in_stock=True
    )
    
    # Apply brand/category filters to all queries
    if brand:
        base_qs = base_qs.filter(brand__title__iexact=brand)
    if category:
        base_qs = base_qs.filter(category__title__exact=category)
    
    # Get all available brands and categories
    brands = Product.objects.values_list('brand__title', flat=True).distinct()
    categories = Product.objects.values_list('category__title', flat=True).distinct()
    
    # Main products - show different sets based on item_type
    if item_type == 'Discounted':
        discount_expr = ExpressionWrapper(
            (F('old_price') - F('price')) / F('old_price') * 100,
            output_field=FloatField()
        )
        products = (
            base_qs
            .filter(old_price__gt=F('price'))
            .annotate(discount_pct=discount_expr)
            .order_by('-discount_pct')
        )
    elif item_type == 'New':
        products = base_qs.order_by('-date')
    else:
        products = base_qs.all()  # Default: show all products
    
    # Prepare special sections (always show these)
    popular_items = (
        base_qs
        .annotate(review_count=Count('productreview'))
        .order_by('-review_count', '-date')[:10]
    )
    
    discounted_items = (
        base_qs
        .filter(old_price__gt=F('price'))
        .annotate(discount_pct=ExpressionWrapper(
            (F('old_price') - F('price')) / F('old_price') * 100,
            output_field=FloatField()
        ))
        .order_by('-discount_pct')[:4]
    )
    
    new_items = base_qs.order_by('-date')[:10]
    
    context = {
        'products': products,
        'popular_items': popular_items,
        'discounted_items': discounted_items,
        'new_items': new_items,
        'active_brand': brand,
        'active_category': category,
        'brands': brands,
        'categories': categories,
        "CATEGORY_MAP": CATEGORY_MAP,
        'shop_views': shop_views,
        'active_filter': item_type,  # To highlight active filter in template
    }
    
    return render(request, 'flame/product-list.html', context)
def category_list_view(request):
    categories = Category.objects.all()
    shop_views=Shop.objects.all()
    total_laptops = 0
    total_desktops = 0
    total_accessories = 0


    total_laptops += Product.objects.filter(category__title__iexact="Laptop").count()
    total_desktops += Product.objects.filter(category__title__iexact="Desktop").count()
    total_accessories += Product.objects.filter(category__title__iexact="Accessories").count()
    # categories = Category.objects.all().annotate(product_count=Count("c_id"))
    context = {
        "shop_views": shop_views,
        'laptop_count': total_laptops,
        'desktop_count': total_desktops,
        'accessories_count': total_accessories,
        "categories": categories
    }
    return render(request,'flame/category.html',context)

# Product list with respect to Category
def category_product_list_view(request, cid):
    category = Category.objects.get(c_id=cid)
    products = Product.objects.filter(shop__isnull=False,product_status="published",category=category)
    shop_views=Shop.objects.all()

    context = {
        "shop_views": shop_views,

        "products": products,
        "category": category,
    }
    return render(request,'flame/category-product-list.html', context)

# Product list with respect to brand
def brand_product_list_view(request, bid):
    shop_views=Shop.objects.all()
   
    brand = Brand.objects.get(b_id=bid)
    products = Product.objects.filter(product_status="published",brand=brand,shop__isnull=False)
    context = {
        "shop_views": shop_views,

        "products": products,
        "brand": brand,
    }
    return render(request,'flame/brand-product-list.html', context)
# Shop List View
def shop_list_view(request):

    shop = Shop.objects.all()
    context = {
        'shop': shop,
    }
    return render(request,'flame/shop-list.html',context)
def shop_view(request):
    shop_views = Shop.objects.all()
    context = {
        'shop_views': shop_views,
    }
    return render(request,'partials/base.html',context)

# Shop Detail View
def shop_detail_view(request, sid):
    shop = get_object_or_404(Shop, shop_id=sid)
    products = Product.objects.filter(shop=shop, product_status="published")
    brands = Brand.objects.filter(brand_products__shop=shop).distinct()
    categories = Category.objects.filter(category__shop=shop).distinct()
    shop_views=Shop.objects.all()
    context = {
        'shop': shop,
        'shop_views':shop_views,
        'brands': brands,
        'categories': categories,
        'products': products,
    }
    return render(request, 'Shop/shop.html', context)

# Product List View (With Specific Shop)
def shop_product_list_view(request, sid):
    shop = Shop.objects.get(shop_id=sid)
    products = Product.objects.filter(product_status="published",shop=shop)
    shop_views=Shop.objects.all()

    context = {
        "shop_views": shop_views,

        "products": products,
        "shop": shop,
    }
    return render(request,'flame/shop-product-list.html', context)

# Product Detail View (With Specific Shop)
def shop_product_detail_view(request, pid, sid):
    shop = get_object_or_404(Shop, shop_id = sid)
    product = get_object_or_404(Product, p_id= pid, shop=shop)
    
    products = Product.objects.filter(category=product.category,shop__isnull=False,brand=product.brand).exclude(p_id=pid)[:3]
    reviews = ProductReview.objects.filter(product=product)
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    
    review_form = ProductReviewForm()
    make_review = True
    shop_views=Shop.objects.all()

    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(product=product, user=request.user).count()
        if user_review_count > 0:
            make_review = False

    p_image = ProductImages.objects.filter(product=product).order_by("-date")
    
    current_language = translation.get_language()
    context = {
        "shop_views": shop_views,
        'current_language': current_language,
        "p": product,
        "shop": shop,
        "make_review": make_review,
        "p_image": p_image,
        "average_rating": average_rating,
        "review_form": review_form,
        "reviews": reviews,
        "products": products,
    }
    return render(request, 'flame/shop-product-detail.html', context)

@login_required
# Review view
def ajax_add_review(request,pid):
    product = Product.objects.get(pk=pid)
    user = request.user
   
    review = ProductReview.objects.create(
        user = user,
        product = product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )
    context = {

        'user' : user.username,
        'review' : request.POST['review'],
        'rating' : request.POST['rating'],
        
    }
    
    # Format the date
    review_date = date_format(review.date, 'd M, Y')
    
    average_reviews = ProductReview.objects.filter(product = product).aggregate(rating = Avg('rating'))   
    
    return JsonResponse(
        {
            'bool' : True,
            'context' : context,
            'review': request.POST['review'],
            'rating': request.POST['rating'],
            'date': review_date,  # Send formatted date
            'average_reviews' : average_reviews,
        }
    )     

#search views
def search_view(request):
    shop_views=Shop.objects.all()
    # Get the search term from either 'q' or 'query' parameter
    query = request.GET.get("q") 
    
    # If no query provided, return all products or handle differently
    if not query:
        products = Product.objects.none()  # Return empty queryset by default
        # Alternatively you could return all products:
        # products = Product.objects.filter(shop__isnull=False).order_by("-date")
    else:
        products = Product.objects.filter(
            title__icontains=query,
            shop__isnull=False
        ).order_by("-date")
    if query:
        products = products.filter(title__icontains=query)
    shop_filter = request.GET.get("shop")  # Get shop filter from URL
    # Apply shop filter if exists

    shops = Shop.objects.all()
    
    context = {
        "shop_views": shop_views,
        "shops": shops,
        "products": products,
        "query": query or "" 
    }
    return render(request, 'flame/search.html', context)
# filter product view
def filter_product(request):
    shops = request.GET.getlist("shop[]")
    brands = request.GET.getlist('brand[]')
    
    min_price = request.GET['min_price']
    max_price = request.GET['max_price']
    
    products = Product.objects.filter(product_status="published",shop__isnull=False).order_by('-id').distinct()
    products = products.filter(price__gte=min_price)
    products = products.filter(price__lte=max_price)
    
    if len(brands) > 0:
        products = products.filter(brand__id__in=brands).distinct()
        
    if len(shops) > 0 :
        products = products.filter(shop__id__in=shops).distinct()

    data = render_to_string("flame/async/product-list.html", {"products": products})
    return JsonResponse({"data": data}) 

# Add to cart (With Specific Shop)
# def add_to_shop_cart(request):
#     shop_id  =str(request.GET['sid'])
#     product_id = str(request.GET['id'])
    
#     cart_product = {
#         'title': request.GET['title'],
#         'qty': int(request.GET['qty']),
#         'price': float(request.GET['price']),
#         'image': request.GET['image'],
#         'pid': request.GET['pid'],
#         'sid': shop_id,
#     }
    
#     if 'cart_data' not in request.session:
#         request.session['cart_data'] = {}
        
#     shop_cart = request.session['cart_data'].get(shop_id,{})
    
#     if product_id in shop_cart:
#         shop_cart[product_id]['qty'] = cart_product['qty']
#     else:
#         shop_cart[product_id] = cart_product
        
#     request.session['cart_data'][shop_id] = shop_cart
#     request.session.modified = True
    
#     total_items = sum(len(shop) for shop in request.session['cart_data'].values())
    
#     return JsonResponse({
#         "data": request.session['cart_data'],
#         "totalcartitems": total_items,
#     })

def add_to_shop_cart(request):
    """Add to cart with proper USD price handling"""
    try:
        shop_id = str(request.GET.get('sid'))
        product_id = str(request.GET.get('id'))
        
        # Get and validate price
        price_str = request.GET.get('price', '0')
        
        # Clean price string (remove any non-numeric characters except decimal point)
        import re
        price_str = re.sub(r'[^\d.]', '', str(price_str))
        
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            # If price parsing fails, try to get from database
            try:
                product = Product.objects.get(id=product_id)
                price = float(product.price)
            except Product.DoesNotExist:
                return JsonResponse({
                    'error': 'Product not found',
                    'status': 'error'
                }, status=404)
        
        # Validate price
        if price <= 0:
            return JsonResponse({
                'error': 'Invalid price',
                'status': 'error'
            }, status=400)
        
        # Build cart product
        cart_product = {
            'title': request.GET.get('title', ''),
            'qty': int(request.GET.get('qty', 1)),
            'price': price,  # Store USD price
            'image': request.GET.get('image', ''),
            'pid': request.GET.get('pid', ''),
            'sid': shop_id,
        }
        
        # Initialize cart data if not exists
        if 'cart_data' not in request.session:
            request.session['cart_data'] = {}
        
        cart_data = request.session['cart_data']
        
        # Initialize shop cart if not exists
        if shop_id not in cart_data:
            cart_data[shop_id] = {}
        
        # Add or update product in shop's cart
        if product_id in cart_data[shop_id]:
            # Update quantity if product already in cart
            cart_data[shop_id][product_id]['qty'] = cart_product['qty']
        else:
            # Add new product to cart
            cart_data[shop_id][product_id] = cart_product
        
        request.session['cart_data'] = cart_data
        request.session.modified = True
        
        # Calculate total items across all shops
        total_items = sum(
            item['qty'] 
            for shop in cart_data.values() 
            for item in shop.values()
        )
        
        return JsonResponse({
            'status': 'success',
            'data': cart_data,
            'totalcartitems': total_items,
            'message': 'Product added to cart successfully'
        })
        
    except Exception as e:
        import traceback
        print(f"Error in add_to_shop_cart: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)

def shop_cart_view(request):
    """Cart view with multi-currency display"""
    cart_data = request.session.get('cart_data_obj', {})
    current_language = translation.get_language()
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    # Process cart data for display
    cart_display = {}
    grand_total_usd = Decimal('0')
    total_quantity = 0
    
    for shop_id, shop_cart in cart_data.items():
        try:
            shop = Shop.objects.get(shop_id=shop_id)
            shop_total_usd = Decimal('0')
            shop_quantity = 0
            shop_items = []
            
            for product_id, item in shop_cart.items():
                item_total_usd = Decimal(str(item['price'])) * item['qty']
                shop_total_usd += item_total_usd
                shop_quantity += item['qty']
                
                # Format prices based on language
                if current_language == 'my':
                    price_display = format_myanmar_currency(Decimal(str(item['price'])) * exchange_rate)
                    item_total_display = format_myanmar_currency(item_total_usd * exchange_rate)
                else:
                    price_display = format_usd_currency(Decimal(str(item['price'])))
                    item_total_display = format_usd_currency(item_total_usd)
                
                shop_items.append({
                    'id': product_id,
                    'title': item['title'],
                    'price': item['price'],
                    'price_display': price_display,
                    'qty': item['qty'],
                    'image': item['image'],
                    'pid': item['pid'],
                    'item_total': float(item_total_usd),
                    'item_total_display': item_total_display,
                })
            
            # Format shop total
            if current_language == 'my':
                shop_total_display = format_myanmar_currency(shop_total_usd * exchange_rate)
            else:
                shop_total_display = format_usd_currency(shop_total_usd)
            
            cart_display[shop_id] = {
                'shop': shop,
                'items': shop_items,
                'shop_total': float(shop_total_usd),
                'shop_total_display': shop_total_display,
                'shop_quantity': shop_quantity,
            }
            
            grand_total_usd += shop_total_usd
            total_quantity += shop_quantity
            
        except Shop.DoesNotExist:
            continue
    
    # Format grand total
    if current_language == 'my':
        grand_total_display = format_myanmar_currency(grand_total_usd * exchange_rate)
    else:
        grand_total_display = format_usd_currency(grand_total_usd)
    
    context = {
        'cart_display': cart_display,
        'grand_total': float(grand_total_usd),
        'grand_total_display': grand_total_display,
        'total_quantity': total_quantity,
        'current_language': current_language,
    }
    
    return render(request, 'flame/cart.html', context)

def update_shop_cart(request):
    """Update cart quantity with proper price recalculation"""
    product_id = str(request.GET['id'])
    shop_id = str(request.GET['sid'])
    qty = int(request.GET['qty'])
    
    cart_data = request.session.get('cart_data_obj', {})
    current_language = translation.get_language()
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    if shop_id in cart_data and product_id in cart_data[shop_id]:
        cart_data[shop_id][product_id]['qty'] = qty
        request.session['cart_data_obj'] = cart_data
        
        # Calculate updated totals
        item_price = Decimal(str(cart_data[shop_id][product_id]['price']))
        item_total = item_price * qty
        
        # Calculate shop total
        shop_total = Decimal('0')
        shop_quantity = 0
        for item in cart_data[shop_id].values():
            shop_total += Decimal(str(item['price'])) * item['qty']
            shop_quantity += item['qty']
        
        # Calculate grand total
        grand_total = Decimal('0')
        total_quantity = 0
        for shop_cart in cart_data.values():
            for item in shop_cart.values():
                grand_total += Decimal(str(item['price'])) * item['qty']
                total_quantity += item['qty']
        
        # Format response based on language
        if current_language == 'my':
            response_data = {
                'status': 'success',
                'data': {
                    'item_total': float(item_total),
                    'item_total_display': format_myanmar_currency(item_total * exchange_rate),
                    'shop_total': float(shop_total),
                    'shop_total_display': format_myanmar_currency(shop_total * exchange_rate),
                    'grand_total': float(grand_total),
                    'grand_total_display': format_myanmar_currency(grand_total * exchange_rate),
                    'shop_quantity': shop_quantity,
                    'total_quantity': total_quantity,
                    'shop_id': shop_id,
                }
            }
        else:
            response_data = {
                'status': 'success',
                'data': {
                    'item_total': float(item_total),
                    'shop_total': float(shop_total),
                    'grand_total': float(grand_total),
                    'shop_quantity': shop_quantity,
                    'total_quantity': total_quantity,
                    'shop_id': shop_id,
                }
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error'})

def delete_from_shop_cart(request):
    """Delete from cart with proper shop handling"""
    product_id = str(request.GET['id'])
    shop_id = str(request.GET['sid'])
    
    cart_data = request.session.get('cart_data_obj', {})
    current_language = translation.get_language()
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    if shop_id in cart_data and product_id in cart_data[shop_id]:
        del cart_data[shop_id][product_id]
        
        # Remove shop if empty
        if not cart_data[shop_id]:
            del cart_data[shop_id]
            shop_html = None
        else:
            # Render updated shop section
            shop_html = render_cart_shop_section(shop_id, cart_data[shop_id], current_language)
        
        request.session['cart_data_obj'] = cart_data
        
        # Calculate totals
        grand_total = Decimal('0')
        total_quantity = 0
        shop_total = Decimal('0')
        shop_quantity = 0
        
        if shop_id in cart_data:
            for item in cart_data[shop_id].values():
                shop_total += Decimal(str(item['price'])) * item['qty']
                shop_quantity += item['qty']
        
        for shop_cart in cart_data.values():
            for item in shop_cart.values():
                grand_total += Decimal(str(item['price'])) * item['qty']
                total_quantity += item['qty']
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'shop_html': shop_html,
                'shop_total': float(shop_total),
                'shop_quantity': shop_quantity,
                'grand_total': float(grand_total),
                'total_quantity': total_quantity,
            }
        })
    
    return JsonResponse({'status': 'error'})

def render_cart_shop_section(shop_id, shop_cart, language):
    """Helper function to render shop cart section"""
    from django.template.loader import render_to_string
    
    try:
        shop = Shop.objects.get(shop_id=shop_id)
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
        
        shop_items = []
        shop_total = Decimal('0')
        
        for product_id, item in shop_cart.items():
            item_total = Decimal(str(item['price'])) * item['qty']
            shop_total += item_total
            
            if language == 'my':
                price_display = format_myanmar_currency(Decimal(str(item['price'])) * exchange_rate)
                item_total_display = format_myanmar_currency(item_total * exchange_rate)
            else:
                price_display = format_usd_currency(Decimal(str(item['price'])))
                item_total_display = format_usd_currency(item_total)
            
            shop_items.append({
                'id': product_id,
                'title': item['title'],
                'price_display': price_display,
                'qty': item['qty'],
                'image': item['image'],
                'item_total_display': item_total_display,
            })
        
        if language == 'my':
            shop_total_display = format_myanmar_currency(shop_total * exchange_rate)
        else:
            shop_total_display = format_usd_currency(shop_total)
        
        context = {
            'shop': shop,
            'items': shop_items,
            'shop_total_display': shop_total_display,
            'shop_id': shop_id,
        }
        
        return render_to_string('flame/partials/cart_shop_section.html', context)
    
    except Shop.DoesNotExist:
        return None

# API endpoint for price formatting
def format_price_api(request):
    """API endpoint for dynamic price formatting"""
    price = request.GET.get('price', 0)
    lang = request.GET.get('lang', 'en')
    
    try:
        price_usd = Decimal(str(price))
        
        if lang == 'my':
            rate = ExchangeRate.get_current_rate('USD', 'MMK')
            formatted_price = format_myanmar_currency(price_usd * rate)
        else:
            formatted_price = format_usd_currency(price_usd)
        
        return JsonResponse({
            'formatted_price': formatted_price,
            'success': True
        })
    except:
        return JsonResponse({
            'formatted_price': '$0.00',
            'success': False
        })

    
# Cart View (With Specific Shop)
def shop_cart_view(request):
    current_language = translation.get_language()
    shop_views = Shop.objects.all()
    cart_data = request.session.get('cart_data', {})
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    shop_carts = []
    cart_total_amount = 0
    grand_total_quantity = 0  # Track total quantity of all items

    for shop_id, products in cart_data.items():
        try:
            shop = Shop.objects.get(shop_id=shop_id)
            shop_total = 0
            shop_quantity = 0  # Track total quantity for this shop
            
            for product_id, item in products.items():
                item_total = int(item['qty']) * float(item['price'])
                shop_total += item_total
                shop_quantity += int(item['qty'])  # Sum quantities
                grand_total_quantity += int(item['qty'])  # Add to grand total
            
            
            
            cart_total_amount += shop_total
            shop_carts.append({
                'shop': shop,
                'products': products,
                'total': shop_total,
                'shop_quantity': shop_quantity,  # Total quantity for shop
                'item_count': len(products),     # Distinct product count
            })
        except Shop.DoesNotExist:
            continue

    if grand_total_quantity == 0:
        messages.warning(request, _("Your Cart is Empty"))
        return redirect("flame:home")
    
    return render(request, 'flame/shop-cart.html', {
        'shop_views': shop_views,
        'shop_carts': shop_carts,
        'totalcartitems': grand_total_quantity,  # Total quantity of all items
        'cart_total_amount': cart_total_amount,
    })
      
# # Delete from cart (With Specific Shop)        
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET

#updated
# flame/views.py - Update your delete and update functions

def delete_item_from_shop_cart(request):
    product_id = str(request.GET.get('id'))
    shop_id = str(request.GET.get('sid'))
    current_language = translation.get_language()
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    try:
        if 'cart_data' in request.session:
            cart_data = request.session['cart_data']
            
            if shop_id in cart_data and product_id in cart_data[shop_id]:
                del cart_data[shop_id][product_id]
                
                if not cart_data[shop_id]:
                    del cart_data[shop_id]
                
                request.session.modified = True
                
                # Calculate updated totals
                shop_total = 0
                shop_quantity = 0
                if shop_id in cart_data:
                    for p_id, item in cart_data[shop_id].items():
                        shop_total += int(item['qty']) * float(item['price'])
                        shop_quantity += int(item['qty'])
                
                grand_total = sum(
                    int(item['qty']) * float(item['price']) 
                    for shop in cart_data.values() 
                    for item in shop.values()
                )
                total_quantity = sum(
                    int(item['qty']) 
                    for shop in cart_data.values() 
                    for item in shop.values()
                )
                
                # Prepare shop cart data for rendering
                shop_html = ""
                if shop_id in cart_data:
                    shop = Shop.objects.get(shop_id=shop_id)
                    shop_cart_data = {
                        'shop': shop,
                        'products': cart_data[shop_id],
                        'total': shop_total,
                        'shop_quantity': shop_quantity,
                        'item_count': len(cart_data[shop_id]),
                        'shop_id': shop_id,
                    }
                    
                    # Render with language context
                    from django.template.loader import render_to_string
                    shop_html = render_to_string("flame/async/shop-cart-list.html", {
                        "shop_cart": shop_cart_data,
                        "current_language": current_language,
                        "exchange_rate": exchange_rate,
                    })
                
                return JsonResponse({
                    "status": "success",
                    "data": {
                        "shop_html": shop_html if shop_id in cart_data else None,
                        "grand_total": float(grand_total),
                        "total_quantity": total_quantity,
                        "shop_total": shop_total,
                        "shop_quantity": shop_quantity
                    }
                })
                
        return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def update_shop_cart(request):
    product_id = str(request.GET.get('id'))
    shop_id = str(request.GET.get('sid'))
    new_qty = int(request.GET.get('qty', 1))
    current_language = translation.get_language()
    exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    
    try:
        if 'cart_data' in request.session:
            cart_data = request.session['cart_data']
            
            if shop_id in cart_data and product_id in cart_data[shop_id]:
                cart_data[shop_id][product_id]['qty'] = new_qty
                request.session.modified = True
                
                # Calculate updated totals
                item_total = new_qty * float(cart_data[shop_id][product_id]['price'])
                shop_total = sum(
                    int(item['qty']) * float(item['price']) 
                    for item in cart_data[shop_id].values()
                )
                shop_quantity = sum(
                    int(item['qty']) 
                    for item in cart_data[shop_id].values()
                )
                grand_total = sum(
                    int(item['qty']) * float(item['price']) 
                    for shop in cart_data.values() 
                    for item in shop.values()
                )
                total_quantity = sum(
                    int(item['qty']) 
                    for shop in cart_data.values() 
                    for item in shop.values()
                )
                
                return JsonResponse({
                    "status": "success",
                    "data": {
                        "item_total": float(item_total),
                        "shop_total": float(shop_total),
                        "shop_quantity": shop_quantity,
                        "grand_total": float(grand_total),
                        "total_quantity": total_quantity,
                        "shop_id": shop_id,
                        "product_id": product_id,
                    }
                })
                
        return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# def delete_item_from_shop_cart(request):
#     product_id = str(request.GET.get('id'))
#     shop_id = str(request.GET.get('sid'))
    
#     try:
#         if 'cart_data' in request.session:
#             cart_data = request.session['cart_data']
            
#             if shop_id in cart_data and product_id in cart_data[shop_id]:
#                 del cart_data[shop_id][product_id]
                
#                 if not cart_data[shop_id]:
#                     del cart_data[shop_id]
                
#                 request.session.modified = True
                
#                 # Calculate updated totals
#                 shop_total = 0
#                 shop_quantity = 0
#                 if shop_id in cart_data:
#                     for p_id, item in cart_data[shop_id].items():
#                         shop_total += int(item['qty']) * float(item['price'])
#                         shop_quantity += int(item['qty'])
                
#                 grand_total = sum(
#                     int(item['qty']) * float(item['price']) 
#                     for shop in cart_data.values() 
#                     for item in shop.values()
#                 )
#                 total_quantity = sum(
#                     int(item['qty']) 
#                     for shop in cart_data.values() 
#                     for item in shop.values()
#                 )
                
#                 context = {
#                     "shop_id": shop_id,
#                     "shop_total": shop_total,
#                     "shop_quantity": shop_quantity,
#                     "grand_total": grand_total,
#                     "total_quantity": total_quantity
#                 }
                
#                 return JsonResponse({
#                     "status": "success",
#                     "data": {
#                         "shop_html": render_to_string("flame/async/shop-cart-list.html", {
#                             "shop_cart": {
#                                 "shop": Shop.objects.get(shop_id=shop_id),
#                                 "products": cart_data.get(shop_id, {}),
#                                 "total": float(shop_total),
#                                 "shop_quantity": shop_quantity,
#                                 "item_count": len(cart_data.get(shop_id, {})),
#                                 "shop_id": shop_id,
#                             }
#                         }) if shop_id in cart_data else "",
#                         "grand_total": float(grand_total),
#                         "total_quantity": total_quantity,
#                         "shop_total": shop_total,
#                         "shop_quantity": shop_quantity
#                     }
#                 })
                
#         return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)
# # Update Cart (With Specific Shop)
# def update_shop_cart(request):
#     product_id = str(request.GET.get('id'))
#     shop_id = str(request.GET.get('sid'))
#     new_qty = int(request.GET.get('qty', 1))
    
#     try:
#         if 'cart_data' in request.session:
#             cart_data = request.session['cart_data']
            
#             if shop_id in cart_data and product_id in cart_data[shop_id]:
#                 cart_data[shop_id][product_id]['qty'] = new_qty
#                 request.session.modified = True
                
#                 # Calculate updated totals
#                 item_total = new_qty * float(cart_data[shop_id][product_id]['price'])
#                 shop_total = sum(
#                     int(item['qty']) * float(item['price']) 
#                     for item in cart_data[shop_id].values()
#                 )
#                 shop_quantity = sum(  # Total quantity for shop
#                     int(item['qty']) 
#                     for item in cart_data[shop_id].values()
#                 )
#                 grand_total = sum(
#                     int(item['qty']) * float(item['price']) 
#                     for shop in cart_data.values() 
#                     for item in shop.values()
#                 )
#                 total_quantity = sum(  # Grand total quantity
#                     int(item['qty']) 
#                     for shop in cart_data.values() 
#                     for item in shop.values()
#                 )
                
#                 return JsonResponse({
#                     "status": "success",
#                     "data": {
#                         "item_total": float(item_total),
#                         "shop_total": float(shop_total),
#                         "shop_quantity": shop_quantity,
#                         "grand_total": float(grand_total),
#                         "total_quantity": total_quantity,
#                         "shop_id": shop_id,
#                         "product_id": product_id,
#                     }
#                 })
                
#         return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)
# Checkout View (With Specific Shop)
stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def shop_checkout_view(request, sid):
    from django.utils import translation
    from flame.models import ExchangeRate
    from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency, convert_to_myanmar_numerals
    from decimal import Decimal
    
    shop_views = Shop.objects.all()
    current_language = translation.get_language()
    
    try:
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3500')
    
    try:
        # Get shop first
        shop = Shop.objects.get(shop_id=sid)
        
        # Get cart data for this specific shop
        cart_data = request.session.get('cart_data', {}).get(sid, {})
        
        if not cart_data:
            messages.warning(request, _("Your cart for this shop is empty"))
            return redirect('flame:shop-cart')

        # Calculate order total in USD
        order_total = sum(
            int(item.get('qty', 0)) * float(item.get('price', 0)) 
            for item in cart_data.values()
        )
        
        # Create order
        order = CartOrder.objects.create(
            user=request.user,
            shop=shop,
            price=order_total,
            order_type='shop',
            paid_status=False
        )
        
        # Create order items and prepare display data
        cart_items_display = []
        for product_id, item in cart_data.items():
            # Create order item in database
            CartOrderItem.objects.create(
                order=order,
                item=item.get('title', ''),
                image=item.get('image', ''),
                qty=int(item.get('qty', 1)),
                price=float(item.get('price', 0)),
                total=int(item.get('qty', 1)) * float(item.get('price', 0))
            )
            
            # Prepare display data with currency formatting
            item_data = {
                'title': item.get('title', ''),
                'image': item.get('image', ''),
                'qty': int(item.get('qty', 1)),
                'price': float(item.get('price', 0)),
                'total': int(item.get('qty', 1)) * float(item.get('price', 0))
            }
            
            # Add formatted prices based on language
            if current_language == 'my':
                price_mmk = Decimal(str(item_data['price'])) * exchange_rate
                total_mmk = Decimal(str(item_data['total'])) * exchange_rate
                
                item_data['price_display'] = format_myanmar_currency(price_mmk)
                item_data['total_display'] = format_myanmar_currency(total_mmk)
                item_data['price_usd_display'] = f"(${item_data['price']:.2f})"
                item_data['qty_display'] = convert_to_myanmar_numerals(str(item_data['qty']))
            else:
                item_data['price_display'] = f"${item_data['price']:.2f}"
                item_data['total_display'] = f"${item_data['total']:.2f}"
                item_data['price_usd_display'] = None
                item_data['qty_display'] = str(item_data['qty'])
            
            cart_items_display.append(item_data)

        # Format total for display
        if current_language == 'my':
            total_mmk = Decimal(str(order_total)) * exchange_rate
            cart_total_display = format_myanmar_currency(total_mmk)
            cart_total_usd_display = f"(${order_total:.2f})"
        else:
            cart_total_display = f"${order_total:.2f}"
            cart_total_usd_display = None

        # PayPal configuration (always in USD)
        paypal_dict = {
            'business': shop.paypal_email if shop.paypal_email else settings.PAYPAL_RECEIVER_EMAIL,
            'amount': order_total,
            'item_name': f"Order #{order.id} from {shop.title}",
            'invoice': f"INVOICE-{order.id}",
            'currency_code': "USD",
            'notify_url': request.build_absolute_uri(reverse("flame:paypal-ipn")),
            'return_url': request.build_absolute_uri(reverse("flame:payment-completed", args=[sid])),
            'cancel_url': request.build_absolute_uri(reverse("flame:payment-failed")),
        }
        
        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)
        
        # Get active address
        try:
            active_address = Address.objects.get(user=request.user, status=True)
        except:
            active_address = None
            messages.warning(request, _("Please add a shipping address"))

        context = {
            "shop_views": shop_views,
            'order': order,
            'shop': shop,
            'cart_items': cart_items_display,
            'cart_total_amount': order_total,
            'cart_total_display': cart_total_display,
            'cart_total_usd_display': cart_total_usd_display,
            'paypal_payment_button': paypal_payment_button,
            'active_address': active_address,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'sid': sid,
            'current_language': current_language,
            'exchange_rate': float(exchange_rate),
            'is_myanmar': current_language == 'my',
        }
        
        return render(request, 'flame/checkout.html', context)

    except Shop.DoesNotExist:
        messages.error(request, _("Shop not found"))
        return redirect('flame:shop-cart')
    except Exception as e:
        print(f"Checkout error: {str(e)}")
        messages.error(request, _("An error occurred during checkout"))
        return redirect('flame:shop-cart')
# @login_required
# def shop_checkout_view(request, sid):
#     shop_views=Shop.objects.all()

#     try:
#         shop = Shop.objects.get(shop_id=sid)
#         cart_data = request.session.get('cart_data', {}).get(sid, {})
        
#         if not cart_data:
#             messages.warning(request, "Your cart for this shop is empty")
#             return redirect('flame:cart')

#         # Create order with shop reference
#         order_total = sum(item['qty'] * item['price'] for item in cart_data.values())
#         order = CartOrder.objects.create(
#             user=request.user,
#             shop=shop,
#             price=order_total,
#             order_type='shop'
#         )
        
#         # Create order items
#         for product_id, item in cart_data.items():
#             CartOrderItem.objects.create(
#                 order=order,
#                 # product_id=item['pid'],
#                 item=item['title'],
#                 image=item['image'],
#                 qty=item['qty'],
#                 price=item['price'],
#                 total=item['qty'] * item['price']
#             )

#         # Shop-specific PayPal integration
#         paypal_dict = {
#             'business': shop.paypal_email,  # Use shop's PayPal email
#             'amount': order_total,
#             'item_name': f"Order-{order.id}-{shop.title}",
#             'invoice': f"INVOICE-{order.id}-{sid}",
#             'currency_code': "USD",
#             'notify_url': request.build_absolute_uri(reverse("flame:paypal-ipn")),
#             'return_url': request.build_absolute_uri(reverse("flame:payment-completed", args=[sid])),
#             'cancel_url': request.build_absolute_uri(reverse("flame:payment-failed")),
#         }
        
#         paypal_payment_button = PayPalPaymentsForm(button_type='pay',initial=paypal_dict)
        
#         try:
#             active_address = Address.objects.get(user=request.user, status = True)
#         except:
#             active_address =None
#             messages.warning(request, "Please add a shipping address")
            
        

#         return render(request, 'flame/checkout.html', {
#             "shop_views": shop_views,
#             'order': order,
#             'shop': shop,
#             'cart_total_amount': order_total,
#             'paypal_payment_button': paypal_payment_button,
#             'active_address':active_address,
#             'active_address': active_address,
#             'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
#             'cart_data': cart_data,
#             'sid': sid,
#         })

#     except Shop.DoesNotExist:
#         messages.error(request, "Invalid shop")
#         return redirect('flame:cart')
    

#checkout stripe implementation
@csrf_exempt
def create_checkout_session(request, sid):
    from django.utils import translation
    from flame.models import ExchangeRate
    
    try:
        shop = Shop.objects.get(shop_id=sid)
        user = request.user
        current_language = translation.get_language()
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
        
        # Get cart data from session
        cart_data = request.session.get('cart_data', {}).get(sid, {})
        if not cart_data:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Create line items from cart
        line_items = []
        for item_id, item in cart_data.items():
            # Prepare item name with language support
            item_name = item['title']
            if current_language == 'my':
                # Add MMK price info to item name for clarity
                mmk_price = Decimal(str(item['price'])) * exchange_rate
                from flame.utils.myanmar_utils import convert_to_myanmar_numerals
                mmk_formatted = convert_to_myanmar_numerals(f"{mmk_price:,.0f}")
                item_name = f"{item['title']} ({mmk_formatted} ကျပ်)"
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',  # Always charge in USD
                    'product_data': {
                        'name': item_name,
                    },
                    'unit_amount': int(float(item['price']) * 100),  # Convert to cents
                },
                'quantity': item['qty'],
            })
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(   
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('flame:payment-completed', args=[sid])
            ) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse('flame:payment-failed')),
            metadata={
                'shop_id': sid,
                'user_id': user.id,
                'language': current_language,
                'exchange_rate': str(exchange_rate),
            }
        )
        
        return JsonResponse({
            'session_id': checkout_session.id,
            'checkout_url': checkout_session.url,
            'success_url': request.build_absolute_uri(
                reverse('flame:payment-completed', args=[sid])
            )
        })
    
    except Shop.DoesNotExist:
        return JsonResponse({'error': 'Shop not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# @csrf_exempt
# def create_checkout_session(request, sid):
#     try:
#         shop = Shop.objects.get(shop_id=sid)
#         user = request.user
        
#         # Get cart data from session
#         cart_data = request.session.get('cart_data', {}).get(sid, {})
#         if not cart_data:
#             return JsonResponse({'error': 'Cart is empty'}, status=400)
        
#         # Create line items from cart
#         line_items = []
#         for item_id, item in cart_data.items():
#             line_items.append({
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': item['title'],
#                     },
#                     'unit_amount': int(float(item['price']) * 100),  # Convert to cents
#                 },
#                 'quantity': item['qty'],
#             })
            
        
#         # Create Stripe checkout session
#         checkout_session = stripe.checkout.Session.create(   
#             customer_email=user.email,
#             payment_method_types=['card'],
#             line_items=line_items,
#             mode='payment',
#             success_url=request.build_absolute_uri(
#                 reverse('flame:payment-completed', args=[sid])
#             ) + "?session_id={CHECKOUT_SESSION_ID}",
#             cancel_url=request.build_absolute_uri(reverse('flame:payment-failed')),
#             metadata={
#                 'shop_id': sid,
#                 'user_id': user.id,
#             }
#         )
        
        
#         return JsonResponse({'session_id': checkout_session.id,
#                              'checkout_url': checkout_session.url,
#                              'success_url':  request.build_absolute_uri(reverse('flame:payment-completed', args=[sid])
#                     )
#                              })
    
#     except Shop.DoesNotExist:
#         return JsonResponse({'error': 'Shop not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
    
@require_GET
def stripe_session_status(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'paid': False}, status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return JsonResponse({
            'paid': session.payment_status == 'paid'
        })
    except stripe.error.StripeError:
        return JsonResponse({'paid': False}, status=500)

@login_required
def stripe_payment_completed_view(request, sid):
    shop_views=Shop.objects.all()
    try:
        shop = Shop.objects.get(shop_id=sid)
        session_id = request.GET.get('session_id')
        
        if session_id:
            # Verify payment with Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                # Create order record
                cart_data = request.session.get('cart_data', {}).get(sid, {})
                order_total = sum(item['qty'] * item['price'] for item in cart_data.values())
                
                order = CartOrder.objects.create(
                    user=request.user,
                    shop=shop,
                    price=order_total,
                    order_type='shop',
                    payment_method='stripe',
                    paid_status=True,
                    stripe_payment_intent=session.payment_intent
                )
                
                # Create order items
                for product_id, item in cart_data.items():
                    CartOrderItem.objects.create(
                        order=order,
                        item=item['title'],
                        image=item['image'],
                        qty=item['qty'],
                        price=item['price'],
                        total=item['qty'] * item['price']
                    )
                
                # Clear cart for this shop
                if 'cart_data' in request.session and sid in request.session['cart_data']:
                    del request.session['cart_data'][sid]
                    request.session.modified = True
                
                return render(request, 'flame/payment-completed.html', {
                    'shop_views': shop_views,
                    'order': order,
                    'shop': shop
                })
        
        # If payment not successful
        messages.error(request, "Payment verification failed")
        return redirect('flame:payment-failed')
    
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
        return redirect('flame:payment-failed')
# Stripe Webhook Handler
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle payment success
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase
        fulfill_order(session)

    return HttpResponse(status=200)

def fulfill_order(session):
    order_id = session.metadata.get('order_id')
    try:
        order = CartOrder.objects.get(id=order_id)
        if session.payment_status == 'paid':
            order.paid_status = True
            order.payment_method = 'stripe'
            order.save()
            
            # Add any additional fulfillment logic here
    except CartOrder.DoesNotExist:
        # Handle missing order
        pass


# Payment Completed View (With Specific Shop)
# flame/views.py - Updated payment completed view

@login_required
def shop_payment_completed_view(request, sid):
    from django.utils import translation
    from flame.models import ExchangeRate
    from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency, convert_to_myanmar_numerals
    from decimal import Decimal
    
    shop_views = Shop.objects.all()
    current_language = translation.get_language()
    
    try:
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3500')
    
    try:
        shop = Shop.objects.get(shop_id=sid)
        
        # Get the most recent order for this user and shop
        order = CartOrder.objects.filter(
            user=request.user, 
            shop=shop
        ).order_by('-id').first()
        
        if not order:
            messages.error(request, _("Order not found"))
            return redirect('flame:home')
        
        # Prepare order items with formatted prices
        order_items_display = []
        for item in order.cartorderitem_set.all():
            item_data = {
                'item': item.item,
                'image': item.image,
                'qty': item.qty,
                'price': float(item.price),
                'total': float(item.total),
            }
            
            # Format based on language
            if current_language == 'my':
                price_mmk = Decimal(str(item.price)) * exchange_rate
                total_mmk = Decimal(str(item.total)) * exchange_rate
                
                item_data['price_display'] = format_myanmar_currency(price_mmk)
                item_data['total_display'] = format_myanmar_currency(total_mmk)
                item_data['price_usd'] = f"(${item.price:.2f})"
                item_data['qty_display'] = convert_to_myanmar_numerals(str(item.qty))
            else:
                item_data['price_display'] = f"${item.price:.2f}"
                item_data['total_display'] = f"${item.total:.2f}"
                item_data['price_usd'] = None
                item_data['qty_display'] = str(item.qty)
            
            order_items_display.append(item_data)
        
        # Format order total
        if current_language == 'my':
            total_mmk = Decimal(str(order.price)) * exchange_rate
            order_total_display = format_myanmar_currency(total_mmk)
            order_total_usd = f"(${order.price:.2f})"
            order_id_display = convert_to_myanmar_numerals(str(order.id))
        else:
            order_total_display = f"${order.price:.2f}"
            order_total_usd = None
            order_id_display = str(order.id)
        
        # Clear shop's cart after successful payment
        if 'cart_data' in request.session and sid in request.session['cart_data']:
            del request.session['cart_data'][sid]
            request.session.modified = True

        context = {
            'shop_views': shop_views,
            'order': order,
            'order_items': order_items_display,
            'shop': shop,
            'order_total_display': order_total_display,
            'order_total_usd': order_total_usd,
            'order_id_display': order_id_display,
            'current_language': current_language,
            'exchange_rate': float(exchange_rate),
            'is_myanmar': current_language == 'my',
        }
        
        return render(request, 'flame/payment-completed.html', context)

    except Shop.DoesNotExist:
        messages.error(request, _("Invalid shop"))
        return redirect('flame:home')
    except Exception as e:
        print(f"Payment completed error: {str(e)}")
        messages.error(request, _("An error occurred"))
        return redirect('flame:home')
# @login_required
# def shop_payment_completed_view(request, sid):
#     shop_views=Shop.objects.all()
#     try:
#         shop = Shop.objects.get(shop_id=sid)
#         order = CartOrder.objects.filter(
#             user=request.user, 
#             shop=shop
#         ).order_by('-id').first()
        
#         # Clear shop's cart after successful payment
#         if 'cart_data' in request.session and sid in request.session['cart_data']:
#             del request.session['cart_data'][sid]
#             request.session.modified = True

#         return render(request, 'flame/payment-completed.html', {
#             'shop_views': shop_views,
#             'order': order,
#             'shop': shop
#         })

#     except Shop.DoesNotExist:
#         messages.error(request, "Invalid shop")
#         return redirect('flame:home')


# Payment Failed View
@login_required
def payment_failed_view(request):
    return render(request, 'flame/payment-failed.html')

# Profile View
def customer_profile(request):
    shop_views=Shop.objects.all()

    orders = CartOrder.objects.filter(user=request.user).order_by('-id')
    address = Address.objects.filter(user=request.user)
    
    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")
        
        new_address = Address.objects.create(
            user = request.user,
            address= address,
            mobile = mobile,
        )
        messages.success(request, "Address Added Successfully")
        return redirect('flame:profile')
    
    context ={
        "shop_views": shop_views,

        "orders": orders,
        "address":address,
        
    }
    return render(request, 'flame/profile.html', context)

# Order Detail View (In Profile)
def order_detail(request, id):
    shop_views=Shop.objects.all()
   
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItem.objects.filter(order=order)
    context ={
       "shop_views": shop_views,

       "order_items": order_items,
       
    }
    return render(request, 'flame/order-detail.html', context)

# Address View (In Profile)
def make_address_default(request):
    id = str(request.GET['id'])
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})

# Wishlist view
@login_required
def wishlist_view(request):
    shop_views=Shop.objects.all()
    try:
        wishlist = Wishlist.objects.filter(user=request.user)
    except:
        wishlist = None
    context ={
        "shop_views": shop_views,
        "w": wishlist,
    }
    if not wishlist.exists():
        messages.warning(request, "Your Wishlist is Empty")
        return redirect("flame:home")
    return render(request, 'flame/wishlist.html', context)

# Add to wishlist
def add_to_wishlist(request):
    shop_views=Shop.objects.all()
    product_id = request.GET['id']
    product = Product.objects.get(id =product_id)
    context={}
    
    wishlist_count = Wishlist.objects.filter(product=product,user = request.user).count()
    # print(wishlist_count)
    
    if wishlist_count > 0:
        context = {
            "bool" : True
        }
    else:
        new_wishlist = Wishlist.objects.create(
            product=product, 
            user=request.user)
        context = {
            "shop_views": shop_views,
            "bool" : True,
            "new_item": render_to_string("flame/async/wishlist-item.html", {"w": new_wishlist})
        }
    
    context['wishlist_count'] = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse(context) 

# Remove from wishlist
def remove_from_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist.objects.filter(user=request.user)
    shop_views=Shop.objects.all()
  
    product = get_object_or_404(Wishlist, id=pid, user=request.user)
    product.delete()
    
    context = {
        "shop_views": shop_views,

        "w": wishlist,
        "bool":True,
        "wishlist_count": Wishlist.objects.filter(user=request.user).count()
    }
    # wishlist_json = serializers.serialize('json', wishlist)
    data = render_to_string("flame/async/wishlist-list.html", context)
    return JsonResponse({"data":data,
                         "wishlist_count": context['wishlist_count']})
    
def FAQs(request):
    shop_views=Shop.objects.all()

    return render(request, 'footerComponents/FAQs.html',{'shop_views':shop_views})
    
#################################################################################### Current Using ####################################################################################
#################################################################################### Current Using ####################################################################################
#################################################################################### Current Using ####################################################################################

def product_detail_view(request, pid):
    shop_views=Shop.objects.all()

    product = Product.objects.get(p_id=pid)
    # products = Product.objects.filter(product_status="published",shop=shop)
    # product = get_object_or_404(Product, pid=pid)
    products = Product.objects.filter(category=product.category).exclude(p_id=pid)[:3]# how many related products will appear
    
    #Getting Product Reviews Related to the Product
    reviews = ProductReview.objects.filter(product = product)
    
     #Getting Average
    average_rating = ProductReview.objects.filter(product = product).aggregate(rating = Avg('rating'))
    
    #Product Review Form 
    review_form = ProductReviewForm()
    
    make_review = True
    
    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(product = product, user = request.user).count()
        if user_review_count > 0:
            make_review = False
            
            
    
    # p_image = product.p_images.all()
    p_image = ProductImages.objects.filter(product = product).order_by("-date") #need to check here
    
    context = {
        "shop_views": shop_views,

        "p": product,
        "make_review": make_review,
        "p_image": p_image, 
        "average_rating": average_rating,
        "review_form": review_form,
        "reviews": reviews,
        "products" : products,
    }
    return render(request,'flame/product-detail.html', context)

from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

@require_POST
def increase_quantity(request, shop_id, product_id):
    try:
        # Get or initialize cart data
        cart_data = request.session.get('cart_data', {})
        logger.debug(f"Initial cart data: {cart_data}")
        
        # Convert IDs to strings for consistent access
        shop_key = str(shop_id)
        product_key = str(product_id)
        
        # Debug logging
        logger.debug(f"Attempting to update - Shop: {shop_key}, Product: {product_key}")
        
        # Validate cart structure
        if not isinstance(cart_data, dict):
            cart_data = {}
            request.session['cart_data'] = cart_data
            logger.warning("Reset cart_data as it wasn't a dictionary")
        
        # Ensure shop exists in cart
        if shop_key not in cart_data:
            messages.error(request, "Shop not found in cart")
            logger.warning(f"Shop {shop_key} not found in cart")
            return redirect('cart:cart')
        
        # Ensure product exists in shop
        if product_key not in cart_data[shop_key]:
            messages.error(request, "Product not found in cart")
            logger.warning(f"Product {product_key} not found in shop {shop_key}")
            return redirect('cart:cart')
        
        # Ensure quantity exists
        if 'qty' not in cart_data[shop_key][product_key]:
            cart_data[shop_key][product_key]['qty'] = 1
            logger.warning("Quantity field was missing, initialized to 1")
        else:
            cart_data[shop_key][product_key]['qty'] += 1
        
        # Save changes
        request.session['cart_data'] = cart_data
        request.session.modified = True
        logger.debug(f"Updated cart data: {cart_data}")
        messages.success(request, "Quantity increased successfully")
        
        return redirect('flame:shop-cart')
        
    except Exception as e:
        logger.error(f"Error increasing quantity: {str(e)}", exc_info=True)
        messages.error(request, "Failed to update quantity")
        return redirect('flame:shop-cart')

# Similar improvements for decrease_quantity and remove_item
@require_POST
def decrease_quantity(request, shop_id, product_id):
    try:
        cart_data = request.session.get('cart_data', {})
        shop_key = str(shop_id)
        product_key = str(product_id)
        
        if shop_key not in cart_data or product_key not in cart_data[shop_key]:
            messages.error(request, "Item not found in cart")
            return redirect('cart:cart')
        
        if cart_data[shop_key][product_key]['qty'] > 1:
            cart_data[shop_key][product_key]['qty'] -= 1
            messages.success(request, "Quantity decreased successfully")
        else:
            del cart_data[shop_key][product_key]
            if not cart_data[shop_key]:  # Remove empty shops
                del cart_data[shop_key]
            messages.success(request, "Item removed from cart")
        
        request.session['cart_data'] = cart_data
        request.session.modified = True
        return redirect('flame:shop-cart')
        
    except Exception as e:
        logger.error(f"Error decreasing quantity: {str(e)}", exc_info=True)
        messages.error(request, "Failed to update quantity")
        return redirect('flame:shop-cart')

@require_POST
def remove_item(request, shop_id, product_id):
    try:
        cart_data = request.session.get('cart_data', {})
        shop_key = str(shop_id)
        product_key = str(product_id)
        
        if shop_key in cart_data and product_key in cart_data[shop_key]:
            del cart_data[shop_key][product_key]
            if not cart_data[shop_key]:  # Remove empty shops
                del cart_data[shop_key]
            request.session['cart_data'] = cart_data
            request.session.modified = True
            messages.success(request, "Item removed successfully")
        else:
            messages.error(request, "Item not found in cart")
        
        return redirect('flame:shop-cart')
        
    except Exception as e:
        logger.error(f"Error removing item: {str(e)}", exc_info=True)
        messages.error(request, "Failed to remove item")
        return redirect('flame:shop-cart')
    

def start_kbzpay(request, sid):
    
    shop = Shop.objects.get(shop_id=sid)
    order = CartOrder.objects.all()
    api = settings.KBZPAY["API_BASE_URL"]
    payload = {
        "merchantID":    settings.KBZPAY["MERCHANT_ID"],
        "invoiceNo":     str(order.id),
        "description":   f"Order #{order.id}",
        "amount":        float(order.total_amount),
        "currencyCode":  "MMK",
        "nonceStr":      str(uuid.uuid4()),
        "paymentChannel":["DPAY"]  # KBZPay’s DPAY channel
    }
    signature = sign_pgw_payload(settings.KBZPAY["SECRET_KEY"], payload)
    headers = {"Content-Type": "application/json", "signature": signature}
    resp = requests.post(f"{api}/paymenttoken", json=payload, headers=headers)
    resp.raise_for_status()
    token = resp.json()["paymentToken"]
    # Redirect user to the KBZPay payment page
    frontend = settings.KBZPAY["FRONTEND_URL"]
    # backendRedirectURL is your Django endpoint to receive the callback
    backend_url = request.build_absolute_uri("/payments/kbzpay/callback/")
    redirect_params = {
        "shop": shop,
        "paymentToken":       token,
        "backendRedirectUrl": backend_url,
        "merchantRedirectUrl":request.build_absolute_uri(reverse("flame:payment-completed", args=[sid]))
    }
    # Build query‑string redirect
    qs = "&".join(f"{k}={v}" for k, v in redirect_params.items())
    return redirect(f"{frontend}?{qs}")


@csrf_exempt
def kbzpay_callback(request):
    """
    Receives server‑to‑server notification from 2C2P after the user completes payment.
    """
    payload = json.loads(request.body)
    # 1. Validate signature
    incoming_sig = request.headers.get("signature")
    expected_sig = sign_pgw_payload(settings.KBZPAY["SECRET_KEY"], payload)
    if not hmac.compare_digest(incoming_sig, expected_sig):
        return HttpResponseBadRequest("Invalid signature")
    # 2. Check transaction status
    status = payload.get("status")  # e.g. 'SUCCESS'
    invoice = payload.get("invoiceNo")
    # 3. Update your order in DB
    order = CartOrder.objects.get(pk=invoice)
    order.status = "paid" if status == "SUCCESS" else "failed"
    order.save()
    return JsonResponse({"result":"OK"})
def FAQs(request):
    return render(request, 'footerComponents/FAQs.html')

def About(request):
    return render(request, 'footerComponents/About.html')

def AboutUs(request):
    return render(request, 'footerComponents/AboutUs.html')

def Services(request):
    return render(request, 'footerComponents/Services.html')

def PrivacyPolicy(request):
    return render(request, 'footerComponents/Privacy.html')

def Terms(request):
    return render(request, 'footerComponents/Terms&Condition.html')

def ReturnPolicy(request):
    return render(request, 'footerComponents/ReturnExchange.html')

def ContactUs(request):
    return render(request, 'footerComponents/ContactUs.html')
    
# def cart_view(request):
    
#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
#         return render(request, 'flame/cart.html', {"cart_data":request.session['cart_data_obj'], 'totalcartitems':len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
#     else:
#         messages.warning(request,"Your Cart is Empty")
#         return redirect("flame:home")


# # Add to cart
# def add_to_cart(request):
#     cart_product = {}
    
#     cart_product[str(request.GET['id'])]={
#         'title':request.GET['title'],
#         'qty':int(request.GET['qty']),
#         'price':float(request.GET['price']),
#         'image': request.GET['image'],
#         'pid': request.GET['pid'],
#         'shop_id': request.GET.get('shop_id', None),
#         # 'added_from': 'shop' if request.GET.get('shop_id', None) else 'home',
#     }
    
#     if 'cart_data_obj' in request.session:
#         if str(request.GET['id']) in request.session['cart_data_obj']:
#             cart_data = request.session['cart_data_obj']
#             cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty']) 
#             cart_data.update(cart_data)
#             request.session['cart_data_obj'] = cart_data
#         else:
#             cart_data = request.session['cart_data_obj']
#             cart_data.update(cart_product)
#             request.session['cart_data_obj']  = cart_data
            
#     else: 
#         request.session['cart_data_obj'] = cart_product
#     return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems':len(request.session['cart_data_obj'])})

# def delete_item_from_cart(request):
#     product_id = str(request.GET['id'])
    
#     if 'cart_data_obj' in request.session:
#         if product_id in request.session['cart_data_obj']:
#             cart_data = request.session['cart_data_obj']
#             del request.session['cart_data_obj'][product_id]
#             request.session['cart_data_obj'] = cart_data
    
    
#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
    
#     context = render_to_string("flame/async/cart-list.html", 
#                                {"cart_data":request.session['cart_data_obj'], 
#                                 'totalcartitems':len(request.session['cart_data_obj']), 
#                                 'cart_total_amount':cart_total_amount})
#     return JsonResponse({"data":context, 'totalcartitems':len(request.session['cart_data_obj']),"cart_total_amount": cart_total_amount,})
            
# def update_cart(request):
#     product_id = str(request.GET['id'])
#     product_qty = str(request.GET['qty'])
    
#     if 'cart_data_obj' in request.session:
#         if product_id in request.session['cart_data_obj']:
#             cart_data = request.session['cart_data_obj']
#             cart_data[str(request.GET['id'])]['qty'] = product_qty
#             request.session['cart_data_obj'] = cart_data
    
    
#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
    
#     context = render_to_string("flame/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems':len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
#     return JsonResponse({"data":context, 'totalcartitems':len(request.session['cart_data_obj']),"cart_total_amount": cart_total_amount,})      

# #Check out view
# @login_required
# def checkout_view(request):
    
#     cart_total_amount = 0
#     total_amount = 0
    
#     #Checking cart data object session object exist
#     if 'cart_data_obj' in request.session:
#         #Getting total amount for Paypal
#         for p_id, item in request.session['cart_data_obj'].items():
#             total_amount += int(item['qty']) * float(item['price'])
            
#         #Creating Order Objects
#         order = CartOrder.objects.create(
#             user  =request.user,
#             price = total_amount,
#         )
        
#         #Getting total amount for the Cart
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
            
#             cart_order_product = CartOrderItem.objects.create(
#                 order = order,
#                 invoice_no = "INVOICE_NO-" + str(order.id), #Invoice_no-5 etc.
#                 item = item['title'],
#                 image = item['image'],
#                 qty = item['qty'],
#                 price = item['price'],
#                 total = float(item['qty']) * float(item['price'])
#             )
    
    
#     host = request.get_host()
#     paypal_dict = {
#         'business' : settings.PAYPAL_RECEIVER_EMAIL,
#         'amount' : cart_total_amount,
#         'item_name': "Order-Item-No-" + str(order.id),
#         'invoice' : "INVOICE-NO-" + str(order.id),
#         'currency_code': "USD",
#         'notify_url': 'http://{}{}'.format(host,reverse("flame:paypal-ipn")), 
#         'return_url': 'http://{}{}'.format(host,reverse("flame:payment-completed")), 
#         'cancel_url': 'http://{}{}'.format(host,reverse("flame:payment-failed")), 
        
#     } 
#     paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)
    
#     # cart_total_amount = 0
#     # if 'cart_data_obj' in request.session:
#     #     for p_id, item in request.session['cart_data_obj'].items():
#     #         cart_total_amount += int(item['qty']) * float(item['price'])
            
#     return render(request,'flame/checkout.html',{'cart_data':request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount,'paypal_payment_button':paypal_payment_button})



# #For payment integration 
# @login_required
# def payment_completed_view(request):
    
#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
            
#     return render(request,'flame/payment-completed.html',{'cart_data':request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount})

#################################################################################### Original View Logic ####################################################################################
#################################################################################### Original View Logic ####################################################################################
#################################################################################### Original View Logic ####################################################################################