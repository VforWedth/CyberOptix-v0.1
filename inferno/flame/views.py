import time
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.dateformat import format as date_format
from django.utils import timezone
from django.http import HttpResponse,JsonResponse, HttpResponseBadRequest
from userauths.models import User
from flame.forms import ProductReviewForm,ProductForm
from flame.models import (
    Brand, Product, ExchangeRate, Category, Shop, CartOrder, CartOrderItem,
    ProductImages, ProductReview, Wishlist, Address, OrderStatusHistory,
    UserBehavior, RecommendationList, RecommendationItem, EmailLog,
    InventoryLog, ProductAnalytics, SalesAnalytics, MyanmarState, MyanmarCity,
    MyanmarTownship, ShippingRate
)

from django.db.models import Count,Avg,F, ExpressionWrapper, FloatField
from flame.forms import ProductReviewForm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
from django.views.decorators.http import require_GET, require_POST
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

# Import KBZPay integration functions
from .kbzpay_integration import (
    initiate_kbzpay_payment,
    kbzpay_callback as kbzpay_payment_callback,
    check_payment_status
)

# Import PayPal dynamic payment function
from .paypal_dynamic import create_paypal_payment_with_shipping

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
            review_count=Count('reviews')
        ).order_by('-review_count', '-date')[:10]
    else:
        popular_qs = base_qs.annotate(
            review_count=Count('reviews')
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
        .annotate(review_count=Count('reviews'))
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
def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user
   
    review = ProductReview.objects.create(
        user=user,
        product=product,
        review=request.POST['review'],
        rating=request.POST['rating'],
    )
    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }
    
    # Format the date
    review_date = date_format(review.date, 'd M, Y')
    
    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))   
    
    return JsonResponse({
        'bool': True,
        'context': context,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
        'date': review_date,
        'average_reviews': average_reviews,
    })

@login_required
def enhanced_add_review(request, pid):
    """Enhanced review submission with detailed ratings"""
    product = get_object_or_404(Product, pk=pid)
    
    # Check if user can review this product
    if not product.can_user_review(request.user):
        return JsonResponse({
            'success': False,
            'error': _("You cannot review this product")
        }, status=400)
    
    if request.method == 'POST':
        from flame.forms import EnhancedProductReviewForm
        form = EnhancedProductReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            
            # Check if this is a verified purchase
            from flame.models import CartOrderItem
            has_purchased = CartOrderItem.objects.filter(
                order__user=request.user,
                product=product,
                order__product_status='delivered'
            ).exists()
            
            review.is_verified_purchase = has_purchased
            review.save()
            
            # Track user behavior
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='review',
                session_id=request.session.session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                score=5.0  # High score for review action
            )
            
            # Calculate new averages
            reviews_summary = product.reviews.filter(is_approved=True).aggregate(
                avg_rating=Avg('rating'),
                avg_quality=Avg('quality_rating'),
                avg_value=Avg('value_rating'),
                avg_delivery=Avg('delivery_rating'),
                total_reviews=Count('id')
            )
            
            return JsonResponse({
                'success': True,
                'message': _("Review submitted successfully"),
                'review_data': {
                    'id': review.id,
                    'title': review.title,
                    'review': review.review,
                    'rating': review.rating,
                    'quality_rating': review.quality_rating,
                    'value_rating': review.value_rating,
                    'delivery_rating': review.delivery_rating,
                    'date': date_format(review.date, 'd M, Y'),
                    'user': request.user.username,
                    'is_verified': review.is_verified_purchase,
                },
                'averages': reviews_summary
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def mark_review_helpful(request, review_id):
    """Mark a review as helpful or unhelpful"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    review = get_object_or_404(ProductReview, id=review_id)
    is_helpful = request.POST.get('helpful') == 'true'
    
    from flame.models import ReviewHelpful
    
    # Remove any existing vote by this user
    ReviewHelpful.objects.filter(user=request.user, review=review).delete()
    
    # Add new vote
    ReviewHelpful.objects.create(
        user=request.user,
        review=review,
        is_helpful=is_helpful
    )
    
    # Update review counters
    helpful_count = ReviewHelpful.objects.filter(review=review, is_helpful=True).count()
    unhelpful_count = ReviewHelpful.objects.filter(review=review, is_helpful=False).count()
    
    review.helpful_count = helpful_count
    review.unhelpful_count = unhelpful_count
    review.save()
    
    return JsonResponse({
        'success': True,
        'helpful_count': helpful_count,
        'unhelpful_count': unhelpful_count
    })

@login_required
def report_review(request, review_id):
    """Report an inappropriate review"""
    review = get_object_or_404(ProductReview, id=review_id)
    
    if request.method == 'POST':
        from flame.forms import ReviewReportForm
        form = ReviewReportForm(request.POST)
        
        if form.is_valid():
            # Check if user has already reported this review
            from flame.models import ReviewReport
            existing_report = ReviewReport.objects.filter(
                review=review,
                reported_by=request.user
            ).first()
            
            if existing_report:
                return JsonResponse({
                    'success': False,
                    'error': _("You have already reported this review")
                })
            
            report = form.save(commit=False)
            report.review = review
            report.reported_by = request.user
            report.save()
            
            return JsonResponse({
                'success': True,
                'message': _("Review reported successfully. We will review it shortly.")
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def product_reviews_api(request, product_id):
    """API endpoint for product reviews with pagination and filtering"""
    product = get_object_or_404(Product, id=product_id)
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    rating_filter = request.GET.get('rating')
    sort_by = request.GET.get('sort', '-date')
    verified_only = request.GET.get('verified') == 'true'
    
    # Build queryset
    reviews = product.reviews.filter(is_approved=True)
    
    if rating_filter:
        reviews = reviews.filter(rating=int(rating_filter))
    
    if verified_only:
        reviews = reviews.filter(is_verified_purchase=True)
    
    # Apply sorting
    if sort_by == 'helpful':
        reviews = reviews.order_by('-helpful_count', '-date')
    elif sort_by == 'rating_high':
        reviews = reviews.order_by('-rating', '-date')
    elif sort_by == 'rating_low':
        reviews = reviews.order_by('rating', '-date')
    else:
        reviews = reviews.order_by('-date')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(reviews, per_page)
    page_obj = paginator.get_page(page)
    
    # Serialize reviews
    reviews_data = []
    for review in page_obj:
        reviews_data.append({
            'id': review.id,
            'title': review.title,
            'review': review.review,
            'rating': review.rating,
            'quality_rating': review.quality_rating,
            'value_rating': review.value_rating,
            'delivery_rating': review.delivery_rating,
            'date': review.date.isoformat(),
            'user': review.user.username,
            'is_verified': review.is_verified_purchase,
            'is_featured': review.is_featured,
            'helpful_count': review.helpful_count,
            'unhelpful_count': review.unhelpful_count,
        })
    
    # Get rating breakdown
    rating_breakdown = product.get_rating_breakdown()
    
    data = {
        'reviews': reviews_data,
        'pagination': {
            'page': page_obj.number,
            'total_pages': page_obj.paginator.num_pages,
            'total_reviews': page_obj.paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'summary': {
            'average_rating': product.get_average_rating(),
            'total_reviews': product.get_review_count(),
            'verified_reviews': product.get_verified_review_count(),
            'rating_breakdown': rating_breakdown,
        }
    }
    
    return JsonResponse(data)     

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

# ================================ LOCATION API ENDPOINTS ================================

def get_states_api(request):
    """API endpoint to get all Myanmar states"""
    try:
        from flame.models import MyanmarState
        states = MyanmarState.objects.all().order_by('name')

        states_data = []
        for state in states:
            states_data.append({
                'id': state.id,
                'name': state.name,
                'name_mm': state.name_mm,
                'code': state.code
            })

        return JsonResponse({
            'states': states_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_cities_by_state_api(request):
    """API endpoint to get cities by state"""
    state_id = request.GET.get('state_id')

    if not state_id:
        return JsonResponse({'error': 'State ID required'}, status=400)

    try:
        from flame.models import MyanmarCity
        cities = MyanmarCity.objects.filter(state_id=state_id).order_by('name')

        cities_data = []
        for city in cities:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'name_mm': city.name_mm,
                'is_major_city': city.is_major_city
            })

        return JsonResponse({
            'cities': cities_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_townships_by_city_api(request):
    """API endpoint to get townships by city"""
    city_id = request.GET.get('city_id')

    if not city_id:
        return JsonResponse({'error': 'City ID required'}, status=400)

    try:
        from flame.models import MyanmarTownship
        townships = MyanmarTownship.objects.filter(city_id=city_id).order_by('name')

        townships_data = []
        for township in townships:
            townships_data.append({
                'id': township.id,
                'name': township.name,
                'name_mm': township.name_mm
            })

        return JsonResponse({
            'townships': townships_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def store_checkout_address_api(request):
    """API endpoint to store checkout address data in session"""
    if request.method == 'POST':
        try:
            import json
            address_data = json.loads(request.body)

            # Only require state and city (minimum for delivery)
            if not address_data.get('state') or not address_data.get('city'):
                return JsonResponse({
                    'error': 'State and city are required'
                }, status=400)

            # Clean and store whatever data we have
            cleaned_address_data = {
                'state': str(address_data.get('state', '')),
                'city': str(address_data.get('city', '')),
                'township': str(address_data.get('township', '')),
                'street_address': str(address_data.get('street_address', '')).strip(),
                'landmark': str(address_data.get('landmark', '')).strip(),
                'mobile': str(address_data.get('mobile', '')).strip(),
                'shipping_fee': float(address_data.get('shipping_fee', 0)),
                'timestamp': int(time.time())
            }

            request.session['checkout_address_data'] = cleaned_address_data

            # Add shop-specific session backup
            shop_id = address_data.get('shop_id')
            if shop_id:
                shop_session_key = f'checkout_address_shop_{shop_id}'
                request.session[shop_session_key] = cleaned_address_data

            # Set session expiry if not already set (30 minutes)
            if not request.session.get_expiry_age():
                request.session.set_expiry(1800)  # 30 minutes

            request.session.modified = True

            return JsonResponse({'success': True})

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'error': 'Invalid data format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Failed to store address data'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def calculate_shipping_fee_api(request):
    """API endpoint to calculate shipping fees"""
    shop_id = request.GET.get('shop_id')
    customer_city_id = request.GET.get('customer_city_id')

    if not shop_id or not customer_city_id:
        return JsonResponse({'error': 'Shop ID and Customer City ID required'}, status=400)

    try:
        from flame.models import Shop, MyanmarCity, ShippingRate, ExchangeRate
        from decimal import Decimal

        shop = Shop.objects.get(shop_id=shop_id)
        customer_city = MyanmarCity.objects.get(id=customer_city_id)

        # Get current exchange rate
        try:
            exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
        except:
            exchange_rate = Decimal('3500')

        shipping_fee_mmk = Decimal('0')
        shipping_fee_usd = Decimal('0')

        # Check if shop has location data
        if shop.city and shop.state:
            # Try to find exact shipping rate
            try:
                shipping_rate = ShippingRate.objects.get(
                    shop=shop,
                    from_city=shop.city,
                    to_city=customer_city
                )
                shipping_fee_mmk = shipping_rate.rate_mmk
                shipping_fee_usd = shipping_rate.rate_usd
            except ShippingRate.DoesNotExist:
                # Use default rates based on location relationship
                if shop.city == customer_city:
                    # Same city - free or minimal shipping
                    shipping_fee_mmk = Decimal('1000')  # 1,000 MMK for same city
                    shipping_fee_usd = Decimal('0.30')
                elif shop.state == customer_city.state:
                    # Same state - moderate shipping
                    shipping_fee_mmk = Decimal('3000')  # 3,000 MMK for same state
                    shipping_fee_usd = Decimal('1.00')
                else:
                    # Different state - higher shipping
                    shipping_fee_mmk = Decimal('5000')  # 5,000 MMK for different state
                    shipping_fee_usd = Decimal('1.50')
        else:
            # Shop doesn't have location data - use default
            shipping_fee_mmk = Decimal('3000')
            shipping_fee_usd = Decimal('1.00')

        # Format the results
        current_language = translation.get_language()
        is_myanmar = current_language == 'my'

        from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency

        if is_myanmar:
            shipping_fee_display = format_myanmar_currency(shipping_fee_mmk)
            shipping_fee_alt_display = format_usd_currency(shipping_fee_usd)
        else:
            shipping_fee_display = format_usd_currency(shipping_fee_usd)
            shipping_fee_alt_display = format_myanmar_currency(shipping_fee_mmk)

        return JsonResponse({
            'shipping_fee_mmk': float(shipping_fee_mmk),
            'shipping_fee_usd': float(shipping_fee_usd),
            'shipping_fee_display': shipping_fee_display,
            'shipping_fee_alt_display': shipping_fee_alt_display,
            'is_myanmar': is_myanmar,
            'is_same_city': shop.city == customer_city if shop.city else False,
            'is_same_state': shop.state == customer_city.state if shop.state else False,
            'exchange_rate': float(exchange_rate)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Cart View (With Specific Shop)
def shop_cart_view(request):
    shop_views = Shop.objects.all()
    cart_data = request.session.get('cart_data', {})
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
        messages.warning(request, "Your Cart is Empty")
        return redirect("flame:home")
    
    return render(request, 'flame/shop-cart.html', {
        'shop_views': shop_views,
        'shop_carts': shop_carts,
        'totalcartitems': grand_total_quantity,  # Total quantity of all items
        'cart_total_amount': cart_total_amount,
    })
    
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
def shop_checkout_direct_view(request, sid):
    """Direct address input checkout view - no cache dependencies"""
    from django.utils import translation
    from flame.models import ExchangeRate, MyanmarState, MyanmarCity, MyanmarTownship
    from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency, convert_to_myanmar_numerals
    from decimal import Decimal

    shop_views = Shop.objects.all()
    current_language = translation.get_language()

    try:
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3000')

    try:
        # Get shop
        shop = Shop.objects.get(shop_id=sid)

        # Get cart data for this specific shop
        cart_data = request.session.get('cart_data', {}).get(sid, {})

        if not cart_data:
            messages.warning(request, "Your cart is empty")
            return redirect('flame:shop-cart')

        # Calculate cart total
        cart_total = Decimal('0')
        for item in cart_data.values():
            try:
                price = Decimal(str(item['price']))
                qty = int(item['qty'])
                cart_total += price * qty
            except (ValueError, TypeError, KeyError):
                continue

        # Create or get order
        order, created = CartOrder.objects.get_or_create(
            user=request.user,
            shop=shop,
            price=cart_total,
            order_type='shop',
            payment_status='pending'
        )

        # Get user's active address if exists
        try:
            active_address = request.user.address_set.filter(status=True).first()
        except:
            active_address = None

        context = {
            'shop_views': shop_views,
            'shop': shop,
            'order': order,
            'cart_total': cart_total,
            'cart_total_display': format_usd_currency(cart_total),
            'cart_data': cart_data,
            'sid': sid,
            'exchange_rate': exchange_rate,
            'is_myanmar': current_language == 'my',
            'active_address': active_address,
        }

        # Add currency display for Myanmar users
        if current_language == 'my':
            cart_total_mmk = cart_total * exchange_rate
            context['cart_total_mmk'] = format_myanmar_currency(cart_total_mmk)

        return render(request, 'flame/checkout_direct_input.html', context)

    except Shop.DoesNotExist:
        messages.error(request, "Shop not found")
        return redirect('flame:home')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('flame:home')

def check_offline_redirect(request):
    """Check if request should be redirected to offline version"""
    # Simple offline detection - can be enhanced with more sophisticated logic
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

    # Check for offline indicators
    offline_indicators = [
        request.GET.get('offline') == 'true',
        request.session.get('force_offline'),
        'offline' in user_agent
    ]

    return any(offline_indicators)

def get_offline_redirect_url(original_path, shop_id=None):
    """Get appropriate offline URL for given path"""
    offline_routes = {
        '/checkout/shop/': '/checkout/direct/',
        '/payment/': '/checkout/direct/',
        '/products/': '/offline/',
        '/shop/': '/offline/',
        '/search/': '/offline/',
    }

    for pattern, offline_url in offline_routes.items():
        if original_path.startswith(pattern.replace('/', '')):
            if shop_id and offline_url.endswith('/'):
                return f"{offline_url.rstrip('/')}/{shop_id}/"
            return offline_url

    return '/offline/'

def shop_checkout_view(request, sid):
    from django.utils import translation
    from flame.models import ExchangeRate, MyanmarState, MyanmarCity, MyanmarTownship
    from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency, convert_to_myanmar_numerals
    from decimal import Decimal

    # Check for offline redirect
    if check_offline_redirect(request):
        offline_url = get_offline_redirect_url(request.path, sid)
        return redirect(offline_url)
    
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
            total_amount=order_total,
            order_type='shop',
            paid_status=False,
            payment_method='paypal'  # Default for checkout page
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
            'custom': sid,  # Pass shop_id for signal handler
        }
        
        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)
        
        # Get active address
        try:
            active_address = Address.objects.get(user=request.user, status=True)
        except:
            active_address = None
            messages.warning(request, _("Please add a shipping address"))

        # Get Myanmar location data for the form
        myanmar_states = MyanmarState.objects.all().order_by('name')

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
            'myanmar_states': myanmar_states,
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
@login_required
def create_checkout_session(request, sid):
    from django.utils import translation
    from flame.models import ExchangeRate

    try:
        shop = Shop.objects.get(shop_id=sid)
        user = request.user
        current_language = translation.get_language()
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')

        # Check if user has minimum address data in session
        address_data = request.session.get('checkout_address_data', {})
        if not address_data or not all([
            address_data.get('state'),
            address_data.get('city')
        ]):
            return JsonResponse({
                'error': 'Please select your state and city before proceeding with payment'
            }, status=400)

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

        # Add shipping fee as a line item
        shipping_fee_usd = float(address_data.get('shipping_fee', 0))
        if shipping_fee_usd > 0:
            shipping_name = "Shipping & Delivery"
            if current_language == 'my':
                shipping_mmk = Decimal(str(shipping_fee_usd)) * exchange_rate
                from flame.utils.myanmar_utils import convert_to_myanmar_numerals
                shipping_formatted = convert_to_myanmar_numerals(f"{shipping_mmk:,.0f}")
                shipping_name = f"ပစ္စည်းပို့ခ ({shipping_formatted} ကျပ်)"

            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': shipping_name,
                    },
                    'unit_amount': int(shipping_fee_usd * 100),  # Convert to cents
                },
                'quantity': 1,
            })
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('flame:stripe-payment-completed', args=[sid])
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

                # Try to get address data from session (JavaScript stored it)
                address_data = request.session.get('checkout_address_data', {})
                shipping_fee = float(address_data.get('shipping_fee', 0))
                total_with_shipping = order_total + shipping_fee

                # Build delivery address and get phone - with fallback to user profile
                delivery_address = ""
                delivery_phone = ""

                # Extract mobile from session address data first
                if address_data and address_data.get('mobile'):
                    delivery_phone = str(address_data.get('mobile', '')).strip()

                if address_data and address_data.get('state') and address_data.get('city'):
                    try:
                        from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

                        # Get address components safely
                        state = None
                        city = None
                        township = None

                        try:
                            state = MyanmarState.objects.get(id=address_data.get('state'))
                            city = MyanmarCity.objects.get(id=address_data.get('city'))
                            if address_data.get('township'):
                                township = MyanmarTownship.objects.get(id=address_data.get('township'))
                        except (MyanmarState.DoesNotExist, MyanmarCity.DoesNotExist, MyanmarTownship.DoesNotExist):
                            # If lookup fails, use IDs as strings for basic info
                            pass

                        parts = []
                        if address_data.get('street_address'):
                            parts.append(address_data.get('street_address'))
                        if township:
                            parts.append(township.name)
                        elif address_data.get('township'):
                            parts.append(f"Township ID: {address_data.get('township')}")
                        if city:
                            parts.append(city.name)
                        elif address_data.get('city'):
                            parts.append(f"City ID: {address_data.get('city')}")
                        if state:
                            parts.append(state.name)
                        elif address_data.get('state'):
                            parts.append(f"State ID: {address_data.get('state')}")
                        if address_data.get('landmark'):
                            parts.append(f"Near {address_data.get('landmark')}")

                        delivery_address = ", ".join(parts) if parts else "Address information available"

                    except Exception as e:
                        delivery_address = "Address information available"

                # Fallback: Get address from user's profile if session data failed
                if not delivery_address:
                    try:
                        from flame.models import Address
                        active_address = Address.objects.get(user=request.user, status=True)
                        address_parts = []
                        if active_address.street_address:
                            address_parts.append(active_address.street_address)
                        if active_address.township:
                            address_parts.append(active_address.township.name)
                        if active_address.city:
                            address_parts.append(active_address.city.name)
                        if active_address.state:
                            address_parts.append(active_address.state.name)

                        delivery_address = ", ".join(address_parts) if address_parts else "User's default address"
                        delivery_phone = active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else ""
                    except:
                        delivery_address = "To be confirmed"

                # Get phone number if not already set
                if not delivery_phone:
                    try:
                        from flame.models import Address
                        active_address = Address.objects.get(user=request.user, status=True)
                        delivery_phone = active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else ""
                    except:
                        delivery_phone = "To be confirmed"

                order = CartOrder.objects.create(
                    user=request.user,
                    shop=shop,
                    price=order_total,
                    shipping_cost=shipping_fee,
                    total_amount=total_with_shipping,
                    order_type='shop',
                    payment_method='stripe',
                    paid_status=True,
                    delivery_address=delivery_address,
                    delivery_phone=delivery_phone,
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

                # Redirect to the main payment completed view for consistent display
                return redirect('flame:payment-completed', sid=sid)
        
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
        
        # Format order total and shipping
        if current_language == 'my':
            subtotal_mmk = Decimal(str(order.price)) * exchange_rate
            shipping_mmk = Decimal(str(order.shipping_cost)) * exchange_rate
            total_mmk = Decimal(str(order.total_amount)) * exchange_rate

            order_subtotal_display = format_myanmar_currency(subtotal_mmk)
            order_shipping_display = format_myanmar_currency(shipping_mmk) if order.shipping_cost > 0 else _("Free")
            order_total_display = format_myanmar_currency(total_mmk)
            order_total_usd = f"(${order.total_amount:.2f})"
            order_id_display = convert_to_myanmar_numerals(str(order.id))
        else:
            order_subtotal_display = f"${order.price:.2f}"
            order_shipping_display = f"${order.shipping_cost:.2f}" if order.shipping_cost > 0 else _("Free")
            order_total_display = f"${order.total_amount:.2f}"
            order_total_usd = None
            order_id_display = str(order.id)
        
        # Clear shop's cart after successful payment
        if 'cart_data' in request.session and sid in request.session['cart_data']:
            del request.session['cart_data'][sid]
            request.session.modified = True

        # Get delivery address - fallback to session data if not in order
        delivery_address = order.delivery_address
        delivery_phone = order.delivery_phone

        if not delivery_address:
            # Try to get address from session (for recent payments)
            address_data = request.session.get('checkout_address_data', {})
            if address_data and address_data.get('state') and address_data.get('city'):
                try:
                    from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

                    parts = []
                    if address_data.get('street_address'):
                        parts.append(address_data.get('street_address'))

                    # Add city and state info
                    try:
                        if address_data.get('township'):
                            township = MyanmarTownship.objects.get(id=address_data.get('township'))
                            parts.append(township.name)
                    except:
                        pass

                    try:
                        city = MyanmarCity.objects.get(id=address_data.get('city'))
                        parts.append(city.name)
                    except:
                        parts.append(f"City ID: {address_data.get('city')}")

                    try:
                        state = MyanmarState.objects.get(id=address_data.get('state'))
                        parts.append(state.name)
                    except:
                        parts.append(f"State ID: {address_data.get('state')}")

                    if address_data.get('landmark'):
                        parts.append(f"Near {address_data.get('landmark')}")

                    delivery_address = ", ".join(parts) if parts else "Address selected during checkout"
                except:
                    delivery_address = "Address selected during checkout"

            # Fallback to user profile address
            if not delivery_address:
                try:
                    from flame.models import Address
                    active_address = Address.objects.get(user=request.user, status=True)
                    addr_parts = []
                    if active_address.street_address:
                        addr_parts.append(active_address.street_address)
                    if active_address.township:
                        addr_parts.append(active_address.township.name)
                    if active_address.city:
                        addr_parts.append(active_address.city.name)
                    if active_address.state:
                        addr_parts.append(active_address.state.name)

                    delivery_address = ", ".join(addr_parts) if addr_parts else "User's default address"
                    delivery_phone = active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else delivery_phone
                except:
                    delivery_address = "Delivery address to be confirmed"

        context = {
            'shop_views': shop_views,
            'order': order,
            'order_items': order_items_display,
            'shop': shop,
            'order_subtotal_display': order_subtotal_display,
            'order_shipping_display': order_shipping_display,
            'order_total_display': order_total_display,
            'order_total_usd': order_total_usd,
            'order_id_display': order_id_display,
            'delivery_address': delivery_address,
            'delivery_phone': delivery_phone,
            'payment_method': order.get_payment_method_display(),
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

@login_required
def cod_payment_view(request, sid):
    """Handle Cash on Delivery payment processing"""
    from django.utils import translation
    from flame.models import ExchangeRate
    from flame.utils.myanmar_utils import format_myanmar_currency, format_usd_currency, convert_to_myanmar_numerals
    from decimal import Decimal
    
    if request.method != 'POST':
        return redirect('flame:shop-checkout', sid=sid)
    
    shop_views = Shop.objects.all()
    current_language = translation.get_language()
    
    try:
        exchange_rate = ExchangeRate.get_current_rate('USD', 'MMK')
    except:
        exchange_rate = Decimal('3500')
    
    try:
        # Get shop
        shop = Shop.objects.get(shop_id=sid)
        
        # Get cart data for this specific shop
        cart_data = request.session.get('cart_data', {}).get(sid, {})
        
        if not cart_data:
            messages.error(request, _("Your cart for this shop is empty"))
            return redirect('flame:shop-cart')
        
        # Calculate order total in USD
        order_total = sum(
            int(item.get('qty', 0)) * float(item.get('price', 0)) 
            for item in cart_data.values()
        )
        
        # Get delivery address from form data
        state_id = request.POST.get('state')
        city_id = request.POST.get('city')
        township_id = request.POST.get('township')
        street_address = request.POST.get('street_address')
        landmark = request.POST.get('landmark', '')
        mobile = request.POST.get('mobile', '')
        shipping_fee = float(request.POST.get('shipping_fee', 0))

        if not all([state_id, city_id, street_address]):
            messages.error(request, _("Please fill in your complete delivery address"))
            return redirect('flame:shop-checkout', sid=sid)

        try:
            from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

            state = MyanmarState.objects.get(id=state_id)
            city = MyanmarCity.objects.get(id=city_id, state=state)
            township = None
            if township_id:
                township = MyanmarTownship.objects.get(id=township_id, city=city)

            # Create or update user's address
            address_data = {
                'state': state,
                'city': city,
                'township': township,
                'street_address': street_address,
                'landmark': landmark,
            }

            # Try to get user's active address, create if not exists
            try:
                active_address = Address.objects.get(user=request.user, status=True)
                # Update existing address
                for field, value in address_data.items():
                    setattr(active_address, field, value)
                active_address.save()
            except Address.DoesNotExist:
                # Create new address
                active_address = Address.objects.create(
                    user=request.user,
                    status=True,
                    **address_data
                )

            # Build delivery address string
            delivery_parts = [street_address]
            if township:
                delivery_parts.append(township.name)
            delivery_parts.extend([city.name, state.name])
            if landmark:
                delivery_parts.append(f"Near {landmark}")

            delivery_address = ", ".join(delivery_parts)
            # Prioritize mobile from form over stored address
            delivery_phone = mobile.strip() if mobile and mobile.strip() else (active_address.mobile if hasattr(active_address, 'mobile') and active_address.mobile else "Not provided")

        except (MyanmarState.DoesNotExist, MyanmarCity.DoesNotExist, MyanmarTownship.DoesNotExist):
            messages.error(request, _("Invalid delivery location selected"))
            return redirect('flame:shop-checkout', sid=sid)
        
        # Calculate total with shipping
        total_with_shipping = order_total + shipping_fee

        # Create order with COD payment method
        order = CartOrder.objects.create(
            user=request.user,
            shop=shop,
            price=order_total,
            shipping_cost=shipping_fee,
            total_amount=total_with_shipping,
            order_type='shop',
            paid_status=False,  # COD orders are not paid immediately
            payment_method='cod',
            delivery_address=delivery_address,
            delivery_phone=delivery_phone,
            product_status='pending'  # COD orders start as pending
        )
        
        # Create order items
        for product_id, item in cart_data.items():
            CartOrderItem.objects.create(
                order=order,
                invoice_no=f"INVOICE-COD-{order.id}",
                product_status='pending',
                item=item.get('title', ''),
                image=item.get('image', ''),
                qty=int(item.get('qty', 1)),
                price=float(item.get('price', 0)),
                total=int(item.get('qty', 1)) * float(item.get('price', 0))
            )
        
        # Clear cart for this shop after successful order creation
        if 'cart_data' in request.session and sid in request.session['cart_data']:
            del request.session['cart_data'][sid]
            request.session.modified = True
        
        # Add success message
        messages.success(request, _("Cash on Delivery order placed successfully! You will pay when your order is delivered."))
        
        # Redirect to payment completed page
        return redirect('flame:payment-completed', sid=sid)
        
    except Shop.DoesNotExist:
        messages.error(request, _("Shop not found"))
        return redirect('flame:home')
    except Exception as e:
        messages.error(request, _("An error occurred while processing your order. Please try again."))
        return redirect('flame:shop-checkout', sid=sid)

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

    # Get recent login history for security section
    recent_logins = getattr(request.user, 'login_history', None)
    if recent_logins:
        recent_logins = recent_logins.all()[:5]
    else:
        recent_logins = []

    context ={
        "shop_views": shop_views,
        "orders": orders,
        "address": address,
        "recent_logins": recent_logins,
    }
    return render(request, 'flame/profile.html', context)

# ================================ SHOP PROFILE MANAGEMENT ================================

@login_required
def shop_profile_view(request, shop_id):
    """Shop profile management with location and shipping settings"""
    from django.utils import translation
    from flame.models import MyanmarState, MyanmarCity, MyanmarTownship, ShippingRate
    from flame.forms import ShopLocationForm, ShippingRateForm

    try:
        shop = get_object_or_404(Shop, shop_id=shop_id, user=request.user)

        current_language = translation.get_language()
        myanmar_states = MyanmarState.objects.all().order_by('name')
        myanmar_cities = MyanmarCity.objects.all().order_by('name')

        # Initialize forms
        location_form = ShopLocationForm(instance=shop)
        shipping_form = ShippingRateForm()

        # Get existing shipping rates for this shop
        shipping_rates = ShippingRate.objects.filter(shop=shop).select_related(
            'from_city', 'from_state', 'to_city', 'to_state'
        ).order_by('to_state__name', 'to_city__name')

        # Get recent orders for this shop
        try:
            recent_orders = CartOrder.objects.filter(
                cartorderitem__product__shop=shop
            ).distinct().order_by('-date')[:10]
        except:
            recent_orders = []

        context = {
            'shop': shop,
            'myanmar_states': myanmar_states,
            'myanmar_cities': myanmar_cities,
            'shipping_rates': shipping_rates,
            'recent_orders': recent_orders,
            'location_form': location_form,
            'shipping_form': shipping_form,
            'is_myanmar': current_language == 'my',
            'current_language': current_language,
        }

        return render(request, 'flame/shop_profile.html', context)

    except Shop.DoesNotExist:
        messages.error(request, _("Shop not found or you don't have permission to access it"))
        return redirect('flame:home')

@login_required
def update_shop_location(request, shop_id):
    """Update shop location information"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from flame.forms import ShopLocationForm

        shop = get_object_or_404(Shop, shop_id=shop_id, user=request.user)

        form = ShopLocationForm(request.POST, instance=shop)

        if form.is_valid():
            form.save()

            messages.success(request, _("Shop location updated successfully"))
            return JsonResponse({
                'success': True,
                'message': _("Shop location updated successfully"),
                'shop_address': shop.get_shop_full_address() if hasattr(shop, 'get_shop_full_address') else f"{shop.state}, {shop.city}, {shop.township}"
            })
        else:
            errors = []
            for field, field_errors in form.errors.items():
                errors.extend([f"{field}: {error}" for error in field_errors])
            return JsonResponse({'error': '; '.join(errors)}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def manage_shipping_rates(request, shop_id):
    """Manage shipping rates for a shop"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from flame.models import MyanmarCity, ShippingRate
        from flame.forms import ShippingRateForm
        from decimal import Decimal

        shop = get_object_or_404(Shop, shop_id=shop_id, user=request.user)
        action = request.POST.get('action')

        if action == 'add_rate':
            if not shop.city or not shop.state:
                return JsonResponse({'error': 'Shop location must be set first'}, status=400)

            # Use form for validation
            form_data = {
                'to_city': request.POST.get('to_city_id'),
                'rate_mmk': request.POST.get('rate_mmk'),
                'rate_usd': request.POST.get('rate_usd'),
                'estimated_days': request.POST.get('estimated_days', 3),
                'is_active': request.POST.get('is_active', 'on') == 'on',
            }

            form = ShippingRateForm(form_data)

            if form.is_valid():
                try:
                    to_city = form.cleaned_data['to_city']

                    shipping_rate, created = ShippingRate.objects.update_or_create(
                        shop=shop,
                        from_city=shop.city,
                        to_city=to_city,
                        defaults={
                            'from_state': shop.state,
                            'to_state': to_city.state,
                            'rate_mmk': form.cleaned_data['rate_mmk'],
                            'rate_usd': form.cleaned_data['rate_usd'],
                            'estimated_days': form.cleaned_data['estimated_days'],
                            'is_active': form.cleaned_data['is_active'],
                        }
                    )

                    return JsonResponse({
                        'success': True,
                        'message': _("Shipping rate {} successfully").format(_("created") if created else _("updated")),
                        'rate': {
                            'id': shipping_rate.id,
                            'to_city': to_city.name,
                            'to_state': to_city.state.name,
                            'rate_mmk': float(shipping_rate.rate_mmk),
                            'rate_usd': float(shipping_rate.rate_usd),
                            'estimated_days': shipping_rate.estimated_days,
                            'is_active': shipping_rate.is_active,
                        }
                    })

                except Exception as e:
                    return JsonResponse({'error': 'Failed to save shipping rate'}, status=400)
            else:
                errors = []
                for field, field_errors in form.errors.items():
                    errors.extend([f"{field}: {error}" for error in field_errors])
                return JsonResponse({'error': '; '.join(errors)}, status=400)

        elif action == 'delete_rate':
            rate_id = request.POST.get('rate_id')

            try:
                shipping_rate = ShippingRate.objects.get(id=rate_id, shop=shop)
                shipping_rate.delete()

                return JsonResponse({
                    'success': True,
                    'message': _("Shipping rate deleted successfully")
                })

            except ShippingRate.DoesNotExist:
                return JsonResponse({'error': 'Shipping rate not found'}, status=404)

        elif action == 'toggle_rate':
            rate_id = request.POST.get('rate_id')

            try:
                shipping_rate = ShippingRate.objects.get(id=rate_id, shop=shop)
                shipping_rate.is_active = not shipping_rate.is_active
                shipping_rate.save()

                return JsonResponse({
                    'success': True,
                    'message': _("Shipping rate {} successfully").format(_("activated") if shipping_rate.is_active else _("deactivated")),
                    'is_active': shipping_rate.is_active
                })

            except ShippingRate.DoesNotExist:
                return JsonResponse({'error': 'Shipping rate not found'}, status=404)

        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

from django.views.decorators.http import require_POST, require_GET
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


# Use the imported kbzpay_callback from kbzpay_integration
kbzpay_callback = kbzpay_payment_callback

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

# ================================ ORDER TRACKING & MANAGEMENT VIEWS ================================

@login_required
def order_list_view(request):
    """List all orders for the current user"""
    orders = CartOrder.objects.filter(user=request.user).order_by('-order_date')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(product_status=status_filter)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'status_choices': CartOrder._meta.get_field('product_status').choices,
        'current_status': status_filter,
    }
    
    return render(request, 'flame/orders/order-list.html', context)

@login_required
def order_detail_view(request, order_number):
    """Detailed view of a specific order"""
    order = get_object_or_404(CartOrder, order_number=order_number, user=request.user)
    
    from flame.services.order_service import OrderService
    tracking_info = OrderService.get_order_tracking_info(order)
    
    # Get order items
    order_items = order.cartorderitem_set.all()
    
    context = {
        'order': order,
        'tracking_info': tracking_info,
        'order_items': order_items,
        'can_cancel': order.can_be_cancelled(),
        'can_return': order.can_be_returned(),
    }
    
    return render(request, 'flame/orders/order-detail.html', context)

@login_required
def track_order_view(request, order_number):
    """Track order status and progress"""
    order = get_object_or_404(CartOrder, order_number=order_number, user=request.user)
    
    from flame.services.order_service import OrderService
    tracking_info = OrderService.get_order_tracking_info(order)
    
    # Track user behavior
    UserBehavior.objects.create(
        user=request.user,
        action='track_order',
        session_id=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR'),
    )
    
    context = {
        'order': order,
        'tracking_info': tracking_info,
        'status_history': tracking_info['status_history'],
        'progress_percentage': tracking_info['progress_percentage'],
    }
    
    return render(request, 'flame/orders/track-order.html', context)

@login_required 
def cancel_order_view(request, order_number):
    """Cancel an order"""
    order = get_object_or_404(CartOrder, order_number=order_number, user=request.user)
    
    if not order.can_be_cancelled():
        messages.error(request, _("This order cannot be cancelled"))
        return redirect('flame:order-detail', order_number=order_number)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        from flame.services.order_service import OrderService
        OrderService.update_order_status(
            order=order,
            new_status='cancelled',
            user=request.user,
            notes=f"Cancelled by customer. Reason: {reason}"
        )
        
        # Send notification
        from flame.services.notification_service import NotificationService
        NotificationService.send_order_notification(order, 'cancelled')
        
        messages.success(request, _("Your order has been cancelled successfully"))
        return redirect('flame:order-detail', order_number=order_number)
    
    context = {
        'order': order,
    }
    
    return render(request, 'flame/orders/cancel-order.html', context)

@login_required
def return_order_view(request, order_number):
    """Request order return"""
    order = get_object_or_404(CartOrder, order_number=order_number, user=request.user)
    
    if not order.can_be_returned():
        messages.error(request, _("This order cannot be returned"))
        return redirect('flame:order-detail', order_number=order_number)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        from flame.services.order_service import OrderService
        OrderService.update_order_status(
            order=order,
            new_status='returned',
            user=request.user,
            notes=f"Return requested by customer. Reason: {reason}"
        )
        
        messages.success(request, _("Return request submitted successfully"))
        return redirect('flame:order-detail', order_number=order_number)
    
    context = {
        'order': order,
    }
    
    return render(request, 'flame/orders/return-order.html', context)

def order_status_api(request, order_number):
    """API endpoint for order status updates"""
    try:
        if request.user.is_authenticated:
            order = CartOrder.objects.get(order_number=order_number, user=request.user)
        else:
            # Allow guest tracking with email verification
            email = request.GET.get('email')
            if not email:
                return JsonResponse({'error': 'Email required for guest tracking'}, status=400)
            order = CartOrder.objects.get(order_number=order_number, user__email=email)
        
        from flame.services.order_service import OrderService
        tracking_info = OrderService.get_order_tracking_info(order)
        
        data = {
            'order_number': order.order_number,
            'status': order.product_status,
            'status_display': order.get_product_status_display(),
            'progress_percentage': tracking_info['progress_percentage'],
            'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            'tracking_number': order.tracking_number,
            'last_update': tracking_info.get('last_update').isoformat() if tracking_info.get('last_update') else None,
            'current_location': tracking_info.get('current_location', ''),
        }
        
        return JsonResponse(data)
        
    except CartOrder.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ================================ RECOMMENDATION VIEWS ================================

@login_required
def user_recommendations_view(request):
    """Show personalized recommendations for user"""
    # Get active recommendation lists
    recommendations = RecommendationList.objects.filter(
        user=request.user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).prefetch_related('recommendationitem_set__product')
    
    # Group recommendations by type
    recommendation_groups = {}
    for rec_list in recommendations:
        rec_type = rec_list.get_recommendation_type_display()
        if rec_type not in recommendation_groups:
            recommendation_groups[rec_type] = []
        
        items = rec_list.recommendationitem_set.all().order_by('rank')[:10]
        recommendation_groups[rec_type].extend([item.product for item in items])
    
    context = {
        'recommendation_groups': recommendation_groups,
    }
    
    return render(request, 'flame/recommendations/user-recommendations.html', context)

def product_recommendations_api(request, product_id):
    """API endpoint for product-based recommendations"""
    try:
        product = Product.objects.get(id=product_id)
        
        # Get similar products
        similar_products = product.get_similar_products(limit=8)
        
        # Get frequently bought together
        frequently_bought = product.get_frequently_bought_together(limit=8)
        
        # Track user behavior
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                product=product,
                action='view',
                session_id=request.session.session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        
        data = {
            'similar_products': [
                {
                    'id': p.id,
                    'title': p.title,
                    'price': float(p.price),
                    'image': p.image.url if p.image else '',
                    'url': f'/product/{p.p_id}/'
                }
                for p in similar_products
            ],
            'frequently_bought': [
                {
                    'id': p.id,
                    'title': p.title,
                    'price': float(p.price),
                    'image': p.image.url if p.image else '',
                    'url': f'/product/{p.p_id}/'
                }
                for p in frequently_bought
            ]
        }
        
        return JsonResponse(data)
        
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ================================ ANALYTICS VIEWS ================================

def analytics_dashboard_view(request):
    """Analytics dashboard for admins"""
    if not request.user.is_staff:
        return redirect('flame:home')

    from datetime import timedelta, date
    from django.db.models import Sum, Count, Avg
    from django.utils import translation

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Calculate actual sales data
    total_sales = CartOrder.objects.filter(
        paid_status=True,
        order_date__date__gte=month_ago
    ).aggregate(total=Sum('price'))['total'] or 0

    total_orders = CartOrder.objects.filter(
        paid_status=True,
        order_date__date__gte=month_ago
    ).count()

    total_products = Product.objects.filter(product_status='published').count()
    total_customers = User.objects.filter(is_staff=False).count()

    # Top products from actual sales data
    top_products = CartOrderItem.objects.filter(
        order__paid_status=True,
        order__order_date__date__gte=week_ago
    ).values('product__title').annotate(
        total_revenue=Sum('total'),
        units_sold=Sum('qty')
    ).order_by('-total_revenue')[:10]

    # Order status distribution
    order_status_dist = CartOrder.objects.filter(
        order_date__date__gte=week_ago
    ).values('product_status').annotate(
        count=Count('id')
    )

    # Monthly sales data for chart
    monthly_sales_data = []
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_sales = CartOrder.objects.filter(
            paid_status=True,
            order_date__year=month_date.year,
            order_date__month=month_date.month
        ).aggregate(total=Sum('price'))['total'] or 0

        monthly_sales_data.append({
            'month': month_date.strftime('%b'),
            'sales': float(month_sales)
        })

    monthly_sales_data.reverse()  # Show chronologically

    # Monthly orders data for chart
    monthly_orders_data = []
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_orders = CartOrder.objects.filter(
            paid_status=True,
            order_date__year=month_date.year,
            order_date__month=month_date.month
        ).count()

        monthly_orders_data.append({
            'month': month_date.strftime('%b'),
            'orders': month_orders
        })

    monthly_orders_data.reverse()

    # Get current language for currency formatting
    current_language = translation.get_language()
    is_myanmar = current_language == 'my'

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'top_products': top_products,
        'order_status_distribution': list(order_status_dist),
        'monthly_sales_data': monthly_sales_data,
        'monthly_orders_data': monthly_orders_data,
        'date_range': f"{week_ago} to {today}",
        'is_myanmar': is_myanmar,
        'current_language': current_language,
    }

    return render(request, 'flame/analytics.html', context)

def sales_report_api(request):
    """API endpoint for sales reports"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    from datetime import datetime, timedelta
    
    # Get date range from query params
    days = int(request.GET.get('days', 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get sales data
    sales_data = SalesAnalytics.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    data = {
        'labels': [item.date.strftime('%Y-%m-%d') for item in sales_data],
        'revenue': [float(item.total_revenue) for item in sales_data],
        'orders': [item.total_orders for item in sales_data],
        'customers': [item.new_customers + item.returning_customers for item in sales_data],
    }
    
    return JsonResponse(data)

# ================================ EMAIL NOTIFICATION VIEWS ================================

@login_required
def email_preferences_view(request):
    """User email notification preferences"""
    if request.method == 'POST':
        # Update user email preferences
        # This would typically involve a UserProfile or EmailPreference model
        messages.success(request, _("Email preferences updated successfully"))
        return redirect('flame:email-preferences')
    
    # Get user's email logs for display
    recent_emails = EmailLog.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    
    context = {
        'recent_emails': recent_emails,
    }
    
    return render(request, 'flame/email/preferences.html', context)

def email_unsubscribe_view(request, user_id):
    """Unsubscribe from email notifications"""
    try:
        user = User.objects.get(id=user_id)
        # Implement unsubscribe logic here
        # This would typically involve updating user preferences
        
        messages.success(request, _("You have been unsubscribed from email notifications"))
        
    except User.DoesNotExist:
        messages.error(request, _("Invalid unsubscribe link"))
    
    return render(request, 'flame/email/unsubscribe.html')

# ================================ ADVANCED PRODUCT VIEWS ================================

def product_analytics_view(request, product_id):
    """Product analytics for shop owners"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check permissions
    if not (request.user.is_staff or 
            (product.shop and product.shop.user == request.user)):
        return redirect('flame:home')
    
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get product analytics
    analytics = ProductAnalytics.objects.filter(
        product=product,
        date__gte=thirty_days_ago.date()
    ).order_by('date')
    
    # Get reviews summary
    reviews_summary = product.reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
        verified_reviews=Count('id', filter=Q(is_verified_purchase=True))
    )
    
    # Get inventory logs
    inventory_logs = InventoryLog.objects.filter(
        product=product
    ).order_by('-timestamp')[:20]
    
    context = {
        'product': product,
        'analytics': analytics,
        'reviews_summary': reviews_summary,
        'inventory_logs': inventory_logs,
    }
    
    return render(request, 'flame/analytics/product-analytics.html', context)

# ================================ INVENTORY MANAGEMENT VIEWS ================================

@login_required
def inventory_dashboard_view(request):
    """Inventory management dashboard"""
    if not request.user.is_staff:
        return redirect('flame:home')
    
    # Get low stock products
    low_stock_products = Product.objects.filter(
        stock_count__lte=F('min_stock_level')
    ).order_by('stock_count')[:20]
    
    # Get out of stock products
    out_of_stock_products = Product.objects.filter(
        stock_count=0
    )[:20]
    
    # Recent inventory movements
    recent_logs = InventoryLog.objects.order_by('-timestamp')[:50]
    
    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'recent_logs': recent_logs,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
    }
    
    return render(request, 'flame/inventory/dashboard.html', context)

@login_required
def bulk_restock_view(request):
    """Bulk restock products"""
    if not request.user.is_staff:
        return redirect('flame:home')
    
    if request.method == 'POST':
        # Process bulk restock
        restock_data = request.POST.getlist('restock_data')
        updated_count = 0
        
        for item in restock_data:
            try:
                product_id, quantity, cost = item.split(',')
                product = Product.objects.get(id=product_id)
                product.restock(int(quantity), Decimal(cost) if cost else None)
                updated_count += 1
            except (ValueError, Product.DoesNotExist):
                continue
        
        messages.success(request, f"Updated stock for {updated_count} products")
        return redirect('flame:inventory-dashboard')
    
    # Get products that need restocking
    products = Product.objects.filter(
        stock_count__lte=F('min_stock_level')
    ).order_by('stock_count')
    
    context = {
        'products': products,
    }
    
    return render(request, 'flame/inventory/bulk-restock.html', context)

# ================================ OFFLINE FUNCTIONALITY VIEWS ================================

def offline_view(request):
    """
    Offline page view for PWA
    Shows what users can do while offline
    """
    return render(request, 'flame/offline.html')

def api_ping(request):
    """
    Simple ping endpoint for connection checking
    Returns 200 OK if server is reachable
    """
    from django.http import JsonResponse

    if request.method == 'HEAD':
        # For HEAD requests, just return empty response
        return JsonResponse({}, status=200)

    return JsonResponse({
        'status': 'ok',
        'timestamp': time.time(),
        'server': 'online'
    })

def force_offline_mode(request):
    """
    Force offline mode for testing
    """
    request.session['force_offline'] = True
    return JsonResponse({
        'status': 'offline_mode_enabled',
        'message': 'Offline mode has been enabled'
    })

def force_online_mode(request):
    """
    Force online mode (disable offline mode)
    """
    request.session['force_offline'] = False
    return JsonResponse({
        'status': 'online_mode_enabled',
        'message': 'Online mode has been enabled'
    })

@login_required
def adminsetting(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    # Get current user settings and system preferences
    user = request.user
    shops = Shop.objects.all()

    # Get notification preferences
    notification_settings = {
        'email_notifications': True,
        'sms_notifications': False,
        'push_notifications': True
    }

    # Get system settings
    system_settings = {
        'currency': 'MMK',
        'language': 'en',
        'timezone': 'Asia/Yangon',
        'tax_rate': 5.0,
        'shipping_enabled': True,
        'maintenance_mode': False
    }

    if request.method == 'POST':
        # Handle settings update
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()
            messages.success(request, _("Profile updated successfully!"))

        elif action == 'update_notifications':
            # Handle notification settings update
            messages.success(request, _("Notification settings updated!"))

        elif action == 'update_system':
            # Handle system settings update
            messages.success(request, _("System settings updated!"))

        return redirect('flame:adminsetting')

    context = {
        'user': user,
        'shops': shops,
        'notification_settings': notification_settings,
        'system_settings': system_settings,
        'available_languages': [('en', 'English'), ('my', 'Myanmar')],
        'available_currencies': [('MMK', 'Myanmar Kyat'), ('USD', 'US Dollar')],
        'timezones': [('Asia/Yangon', 'Myanmar Time')]
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/Admin_Setting.html', context)

    return render(request, 'flame/Admin_Setting.html', context)

@login_required
def adminsecurity(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    # Security analytics data
    from datetime import datetime, timedelta
    from django.contrib.auth.models import User
    from django.db.models import Count, Q

    # Recent login attempts
    recent_logins = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=30)
    ).order_by('-last_login')[:10]

    # Failed orders (security indicator)
    suspicious_orders = CartOrder.objects.filter(
        paid_status=False,
        order_date__gte=timezone.now() - timedelta(days=7)
    ).values('user__email').annotate(count=Count('id')).filter(count__gte=3)

    # IP tracking (mock data - implement with proper logging)
    recent_activities = [
        {'ip': '192.168.1.1', 'action': 'Login', 'user': 'admin@example.com', 'timestamp': timezone.now()},
        {'ip': '10.0.0.1', 'action': 'Order Created', 'user': 'user@example.com', 'timestamp': timezone.now() - timedelta(hours=1)},
    ]

    # Security settings
    security_settings = {
        'two_factor_enabled': False,
        'login_attempts_limit': 5,
        'session_timeout': 30,
        'password_expiry': 90,
        'ip_whitelist_enabled': False,
        'audit_logging': True
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_security':
            # Handle security settings update
            messages.success(request, _("Security settings updated successfully!"))

        elif action == 'change_password':
            # Handle password change
            messages.success(request, _("Password changed successfully!"))

        elif action == 'enable_2fa':
            # Handle 2FA setup
            messages.success(request, _("Two-factor authentication enabled!"))

        return redirect('flame:adminsecurity')

    context = {
        'recent_logins': recent_logins,
        'suspicious_orders': suspicious_orders,
        'recent_activities': recent_activities,
        'security_settings': security_settings,
        'total_users': User.objects.count(),
        'active_sessions': 5,  # Mock data
        'failed_login_attempts': 12,  # Mock data
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/Admin_security.html', context)

    return render(request, 'flame/Admin_security.html', context)

@login_required
def adminnoti(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    from datetime import timedelta

    # Recent notifications data
    recent_orders = CartOrder.objects.filter(
        order_date__gte=timezone.now() - timedelta(days=7)
    ).order_by('-order_date')[:10]

    # Low stock products
    low_stock_products = Product.objects.filter(
        stock_count__lte=10,
        stock_count__gt=0
    )[:10]

    # Out of stock products
    out_of_stock_products = Product.objects.filter(
        stock_count=0
    )[:10]

    # Recent reviews that need attention
    low_rating_reviews = ProductReview.objects.filter(
        rating__lte=2,
        date__gte=timezone.now() - timedelta(days=7)
    ).select_related('product', 'user')[:10]

    # System notifications
    notifications = [
        {
            'id': 1,
            'title': _('New Order Received'),
            'message': _('You have 5 new orders to process'),
            'type': 'order',
            'timestamp': timezone.now(),
            'read': False,
            'priority': 'high'
        },
        {
            'id': 2,
            'title': _('Low Stock Alert'),
            'message': _('10 products are running low on stock'),
            'type': 'inventory',
            'timestamp': timezone.now() - timedelta(hours=2),
            'read': False,
            'priority': 'medium'
        },
        {
            'id': 3,
            'title': _('Payment Received'),
            'message': _('Payment confirmed for Order #ORD-001'),
            'type': 'payment',
            'timestamp': timezone.now() - timedelta(hours=5),
            'read': True,
            'priority': 'low'
        },
    ]

    # Notification settings
    notification_preferences = {
        'email_orders': True,
        'email_payments': True,
        'email_inventory': True,
        'email_reviews': False,
        'sms_urgent': True,
        'push_all': True
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'mark_read':
            notification_id = request.POST.get('notification_id')
            # Mark notification as read
            messages.success(request, _("Notification marked as read"))

        elif action == 'update_preferences':
            # Update notification preferences
            messages.success(request, _("Notification preferences updated!"))

        return redirect('flame:adminnoti')

    context = {
        'notifications': notifications,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'low_rating_reviews': low_rating_reviews,
        'notification_preferences': notification_preferences,
        'unread_count': len([n for n in notifications if not n['read']]),
        'urgent_count': len([n for n in notifications if n['priority'] == 'high'])
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/Admin_Noti.html', context)

    return render(request, 'flame/Admin_Noti.html', context)

@login_required
def admindash(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    from datetime import timedelta
    from django.db.models import Sum, Count, Avg, Q

    # Dashboard metrics
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Sales metrics
    today_sales = CartOrder.objects.filter(
        paid_status=True,
        order_date__date=today
    ).aggregate(total=Sum('price'))['total'] or 0

    yesterday_sales = CartOrder.objects.filter(
        paid_status=True,
        order_date__date=yesterday
    ).aggregate(total=Sum('price'))['total'] or 0

    # Calculate growth percentage
    sales_growth = ((today_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0

    # Order metrics
    total_orders = CartOrder.objects.count()
    pending_orders = CartOrder.objects.filter(product_status='pending').count()
    completed_orders = CartOrder.objects.filter(product_status='delivered').count()

    # Product metrics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(product_status='published').count()
    low_stock_count = Product.objects.filter(stock_count__lte=10).count()

    # Customer metrics
    total_customers = User.objects.filter(is_staff=False).count()
    new_customers_today = User.objects.filter(
        date_joined__date=today,
        is_staff=False
    ).count()

    # Revenue data for chart (last 7 days)
    revenue_data = []
    labels = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        revenue = CartOrder.objects.filter(
            paid_status=True,
            order_date__date=date
        ).aggregate(total=Sum('price'))['total'] or 0
        revenue_data.append(float(revenue))
        labels.append(date.strftime('%b %d'))

    # Top selling products
    top_products = CartOrderItem.objects.filter(
        order__paid_status=True,
        order__order_date__gte=week_ago
    ).values(
        'product__title',
        'product__image'
    ).annotate(
        total_sold=Sum('qty'),
        revenue=Sum('total')
    ).order_by('-revenue')[:5]

    # Recent orders
    recent_orders = CartOrder.objects.select_related('user').order_by('-order_date')[:10]

    # Order status distribution
    order_status_data = CartOrder.objects.values('product_status').annotate(
        count=Count('id')
    ).order_by('product_status')

    context = {
        # Sales metrics
        'today_sales': today_sales,
        'yesterday_sales': yesterday_sales,
        'sales_growth': round(sales_growth, 2),

        # Order metrics
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,

        # Product metrics
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_count': low_stock_count,

        # Customer metrics
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,

        # Chart data
        'revenue_data': revenue_data,
        'revenue_labels': labels,

        # Lists
        'top_products': top_products,
        'recent_orders': recent_orders,
        'order_status_data': order_status_data,

        # Additional metrics
        'avg_order_value': CartOrder.objects.filter(paid_status=True).aggregate(
            avg=Avg('price'))['avg'] or 0,
        'conversion_rate': 4.2,  # Mock data - calculate based on actual visits
        'total_revenue': CartOrder.objects.filter(paid_status=True).aggregate(
            total=Sum('price'))['total'] or 0,

        # Users data for User AdminDash
        'users': User.objects.all().order_by('-date_joined')[:50],  # Limit to 50 recent users for performance
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/User_AdminDash.html', context)

    return render(request, 'flame/User_AdminDash.html', context)

# Load your dialogs from JSON once at startup
import os
import json

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# dialogs_path = os.path.join(BASE_DIR, "chatbot-training", "chat_data.json")

# with open(dialogs_path, "r", encoding="utf-8") as f:
#     dialog_pairs = json.load(f)

def orders(request):
    from django.utils import translation

    shop_views=Shop.objects.all()

    # Show all orders for staff members, personal orders for regular users
    if request.user.is_staff:
        orders = CartOrder.objects.select_related('user', 'shop').all().order_by('-id')
    else:
        orders = CartOrder.objects.filter(user=request.user).order_by('-id')

    address = Address.objects.filter(user=request.user)

    # Get current language for currency formatting
    current_language = translation.get_language()
    is_myanmar = current_language == 'my'
    
    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")
        
        new_address = Address.objects.create(
            user = request.user,
            address= address,
            mobile = mobile,
        )
        messages.success(request, "Address Added Successfully")
        return redirect('flame:orders')
    
    context ={
        "shop_views": shop_views,
        "orders": orders,
        "address":address,
        "current_language": current_language,
        "is_myanmar": is_myanmar,
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, "flame/Orders.html", context)

    return render(request, "flame/Orders.html", context)

@login_required
def products(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    from django.db.models import Count, Sum, Avg

    # Get all products with additional data for admin panel
    products = Product.objects.select_related(
        'category', 'brand', 'shop', 'user'
    ).prefetch_related(
        'reviews'
    ).annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-date')

    # Filter options
    category_filter = request.GET.get('category')
    brand_filter = request.GET.get('brand')
    shop_filter = request.GET.get('shop')
    status_filter = request.GET.get('status')

    if category_filter:
        products = products.filter(category__id=category_filter)
    if brand_filter:
        products = products.filter(brand__id=brand_filter)
    if shop_filter:
        products = products.filter(shop__id=shop_filter)
    if status_filter:
        products = products.filter(product_status=status_filter)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # Additional data
    shops = Shop.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()

    # Statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(product_status='published').count()
    low_stock_products = Product.objects.filter(stock_count__lte=10).count()
    out_of_stock_products = Product.objects.filter(stock_count=0).count()

    context = {
        "shop_views": shops,
        "products": products,
        "categories": categories,
        "brands": brands,
        "shops": shops,

        # Filter values for maintaining state
        "selected_category": category_filter,
        "selected_brand": brand_filter,
        "selected_shop": shop_filter,
        "selected_status": status_filter,

        # Statistics
        "total_products": total_products,
        "active_products": active_products,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,

        # Status choices
        "status_choices": [
            ('draft', _('Draft')),
            ('published', _('Published')),
            ('disabled', _('Disabled')),
            ('rejected', _('Rejected')),
            ('in_review', _('In Review')),
        ],

        # Myanmar states for shop filtering
        "states": MyanmarState.objects.all(),
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, "flame/products.html", context)

    return render(request, "flame/products.html", context)
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, user=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user   # ✅ auto-assign logged-in user
            product.save()
            return JsonResponse({
                'success': True,
                'message': 'Order updated successfully!',
                'product_id': product.id
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors.get_json_data()
        }, status=400)

    form = ProductForm(instance=product)
    return render(request, 'flame/editproduct.html', {
        'product': product,
        'form': form,
        'shops': Shop.objects.all(),
        'category': Category.objects.all()
    })


@login_required
def add_product(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:home')

    # Get required data for form
    categories = Category.objects.all()
    brands = Brand.objects.all()
    shops = Shop.objects.all()
    states = MyanmarState.objects.all()

    # Import STATUS from models to get product status choices
    from .models import STATUS

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user

            # Set default shop if not specified and user is not superuser
            if not product.shop and not request.user.is_superuser:
                user_shop = shops.filter(user=request.user).first()
                if user_shop:
                    product.shop = user_shop
                else:
                    default_shop = shops.first()
                    if default_shop:
                        product.shop = default_shop

            product.save()

            # Log inventory creation
            InventoryLog.objects.create(
                product=product,
                action='created',
                quantity_before=0,
                quantity_after=product.stock_count,
                user=request.user,
                notes=f"Product created: {product.title}"
            )

            messages.success(request, _("Product added successfully!"))

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "message": str(_("Product added successfully!")),
                    "product_id": product.id
                })
            else:
                return redirect('flame:adminproducts')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
            else:
                messages.error(request, _("Please correct the errors below."))
    else:
        form = ProductForm()

    context = {
        'form': form,
        'categories': categories,
        'brands': brands,
        'shops': shops,
        'states': states,
        'page_title': _('Add New Product'),
        'is_edit': False,
        'status_choices': STATUS,  # Product status choices
    }

    return render(request, "flame/addproduct.html", context)

def chat_page(request):
    return render(request, 'flame/chatbot.html.html')
def recommendation_page(request):
    recommendations = []

    if request.method == 'POST':
        try:
            import pandas as pd
            from sklearn.preprocessing import MinMaxScaler
            from sklearn.metrics.pairwise import cosine_similarity
            import os
            from django.conf import settings

            # Try to find the CSV file in the project
            csv_path = 'products.csv'
            if not os.path.exists(csv_path):
                csv_path = os.path.join(settings.BASE_DIR, 'products.csv')

            if not os.path.exists(csv_path):
                return render(request, 'flame/recommendation.html', {
                    'recommendations': [],
                    'error': 'Product data file not found. Please add products.csv to the project.'
                })

            # Load dataset
            df = pd.read_csv(csv_path, encoding='latin1')

            # Convert RAM to numeric
            def ram_to_gb(ram_str):
                if pd.isna(ram_str):
                    return 0
                ram_str = str(ram_str)
                if 'GB' in ram_str:
                    return int(ram_str.replace('GB','').strip())
                elif 'TB' in ram_str:
                    return int(float(ram_str.replace('TB','').strip())*1024)
                else:
                    return 0

            df.columns = df.columns.str.upper().str.strip()
            df['RAM_Numeric'] = df['RAM'].apply(ram_to_gb)

            # Convert CPU to numeric score
            cpu_mapping = {'i3':3, 'i5':5, 'i7':7, 'i9':9,
                           'ryzen 3':3, 'ryzen 5':5, 'ryzen 7':7, 'ryzen 9':9}

            def cpu_to_score(cpu_str):
                if pd.isna(cpu_str):
                    return 0
                cpu_str = cpu_str.lower()
                for key in cpu_mapping:
                    if key in cpu_str:
                        return cpu_mapping[key]
                return 0

            df['CPU_Numeric'] = df['CPU'].apply(cpu_to_score)

            # Normalize CPU & RAM
            scaler = MinMaxScaler()
            df[['CPU_Norm','RAM_Norm']] = scaler.fit_transform(df[['CPU_Numeric','RAM_Numeric']])

            purpose_vectors = {
                'gaming': {'CPU':8, 'RAM':16},
                'office': {'CPU':5, 'RAM':8},
                'business': {'CPU':7, 'RAM':16},
                'general': {'CPU':5, 'RAM':4}
            }

            purpose = request.POST.get('purpose','').lower().strip()
            if purpose in purpose_vectors:
                target_cpu = purpose_vectors[purpose]['CPU']
                target_ram = purpose_vectors[purpose]['RAM']

                # Normalize target vector using same scaler
                target_scaled = scaler.transform([[target_cpu, target_ram]])

                # Compute cosine similarity
                feature_matrix = df[['CPU_Norm','RAM_Norm']].values
                similarities = cosine_similarity(feature_matrix, target_scaled).flatten()

                df['SIM_SCORE'] = similarities
                top_laptops = df.sort_values(by='SIM_SCORE', ascending=False).head(5)
                recommendations = top_laptops.to_dict('records')

        except ImportError:
            return render(request, 'flame/recommendation.html', {
                'recommendations': [],
                'error': 'Required libraries (pandas, sklearn) not installed.'
            })
        except Exception as e:
            return render(request, 'flame/recommendation.html', {
                'recommendations': [],
                'error': f'Error processing recommendations: {str(e)}'
            })

    return render(request, 'flame/recommendation.html', {'recommendations': recommendations})

@login_required
def admindashboard(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    from datetime import timedelta
    from django.db.models import Sum, Count, Avg, Q
    from django.utils import translation

    # Dashboard metrics
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Sales metrics
    total_sales = CartOrder.objects.filter(paid_status=True).aggregate(total=Sum('price'))['total'] or 0
    today_sales = CartOrder.objects.filter(
        paid_status=True,
        order_date__date=today
    ).aggregate(total=Sum('price'))['total'] or 0

    yesterday_sales = CartOrder.objects.filter(
        paid_status=True,
        order_date__date=yesterday
    ).aggregate(total=Sum('price'))['total'] or 0

    # Calculate growth percentage
    sales_growth = ((today_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0

    # Debug print (remove in production)
    print(f"DEBUG: total_sales={total_sales}, today_sales={today_sales}, yesterday_sales={yesterday_sales}, sales_growth={sales_growth}")

    # Order metrics
    total_orders = CartOrder.objects.count()
    pending_orders = CartOrder.objects.filter(product_status='pending').count()
    completed_orders = CartOrder.objects.filter(product_status='delivered').count()

    # User metrics
    total_users = User.objects.count()  # All users (staff + non-staff)
    total_customers = User.objects.filter(is_staff=False).count()  # Only non-staff users
    new_customers_today = User.objects.filter(
        date_joined__date=today,
        is_staff=False
    ).count()

    # Average order value
    avg_order_value = CartOrder.objects.filter(paid_status=True).aggregate(
        avg=Avg('price'))['avg'] or 0

    # Recent orders for the table
    recent_orders = CartOrder.objects.select_related('user').order_by('-order_date')[:10]

    # Get current language for currency formatting
    current_language = translation.get_language()
    is_myanmar = current_language == 'my'

    # Prepare chart data for JSON
    import json
    from django.db.models.functions import TruncMonth

    # Sales by category for chart
    category_sales = CartOrderItem.objects.filter(
        order__paid_status=True
    ).values('product__category__title').annotate(
        total_sales=Sum('total')
    ).order_by('-total_sales')[:5]

    category_labels = [item['product__category__title'] or 'Unknown' for item in category_sales]
    category_values = [float(item['total_sales']) for item in category_sales]
    category_colors = ['#4361ee', '#f8961e', '#4cc9f0', '#f72585', '#17a2b8']

    # Monthly sales data for line chart
    monthly_sales = CartOrder.objects.filter(paid_status=True).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total_sales=Sum('price')
    ).order_by('month')

    sales_labels = []
    sales_values = []
    orders_values = []

    from datetime import datetime
    for i in range(12):
        month_date = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_name = month_date.strftime('%b')

        # Get sales for this month
        month_sales = CartOrder.objects.filter(
            paid_status=True,
            order_date__year=month_date.year,
            order_date__month=month_date.month
        ).aggregate(total=Sum('price'))['total'] or 0

        # Get orders for this month
        month_orders = CartOrder.objects.filter(
            paid_status=True,
            order_date__year=month_date.year,
            order_date__month=month_date.month
        ).count()

        sales_labels.insert(0, month_name)
        sales_values.insert(0, float(month_sales))
        orders_values.insert(0, month_orders)

    context = {
        # Sales metrics
        'total_sales': total_sales,
        'today_sales': today_sales,
        'sales_growth': round(sales_growth, 2),

        # Order metrics
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,

        # User metrics
        'total_users': total_users,
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,

        # Additional metrics
        'avg_order_value': avg_order_value,
        'recent_orders': recent_orders,

        # Chart data as JSON strings
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'category_colors': json.dumps(category_colors),
        'sales_labels': json.dumps(sales_labels),
        'sales_values': json.dumps(sales_values),
        'orders_values': json.dumps(orders_values),

        # Language and currency
        'current_language': current_language,
        'is_myanmar': is_myanmar,
    }

    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/dashboardpage.html', context)

    return render(request, 'flame/Dashboard.html', context)
@login_required
def adminsales(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    import logging
    from datetime import timedelta
    from django.db.models import Sum, Count, Avg, Max, F
    from django.db.models.functions import TruncMonth
    from django.utils import translation

    # Set up logging
    logger = logging.getLogger(__name__)

    try:
        # Date filtering
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        if request.GET.get('start_date'):
            start_date = timezone.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        if request.GET.get('end_date'):
            end_date = timezone.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()

        logger.info(f"Admin sales view accessed by {request.user.username} for period {start_date} to {end_date}")

        # Sales analytics
        sales_filter = Q(paid_status=True, order_date__date__gte=start_date, order_date__date__lte=end_date)

        # Top selling products using snapshot data for reliability
        top_products = CartOrderItem.objects.filter(
            order__paid_status=True,
            order__order_date__date__gte=start_date,
            order__order_date__date__lte=end_date
        ).select_related('product').values(
            'item',  # Use snapshot product name instead of FK
            'image',  # Use snapshot image instead of FK
            'price',   # Use snapshot price instead of FK
            'product__image',  # Also get FK image as fallback
            'product__title',  # Also get FK title as fallback
        ).annotate(
            units_sold=Sum('qty'),
            total_revenue=Sum('total'),
            avg_price=Avg('price')
        ).order_by('-total_revenue')[:10]

        # Calculate progress percentage and enhance data
        top_products_list = list(top_products)
        if top_products_list:
            max_revenue = top_products_list[0]['total_revenue'] if top_products_list else 1
            for product in top_products_list:
                # Use snapshot data (more reliable than FK relationships)
                product['product__title'] = product.get('item') or product.get('product__title') or 'Unknown Product'

                # Handle image: prefer FK image over snapshot image
                snapshot_image = product.get('image', '')
                fk_image = product.get('product__image', '')

                # Use FK image if available, otherwise use snapshot image
                if fk_image:
                    product['product__image'] = fk_image
                elif snapshot_image and not snapshot_image.startswith('/media/'):
                    # If snapshot image doesn't start with /media/, add it (for legacy data)
                    product['product__image'] = f"/media/{snapshot_image}" if snapshot_image != 'product.jpg' else ''
                else:
                    product['product__image'] = snapshot_image or ''

                product['product__price'] = product.get('price') or 0

                # Calculate progress percentage (rounded to 1 decimal place)
                product['progress_percentage'] = round(min(100, (product['total_revenue'] / max_revenue * 100)), 1) if max_revenue > 0 else 0

                # Try to get category from FK if product still exists, otherwise fallback
                try:
                    # Attempt to get category for this product name from existing products
                    existing_product = Product.objects.filter(title=product['item']).first()
                    if existing_product and existing_product.category:
                        product['product__category__title'] = existing_product.category.title
                    else:
                        product['product__category__title'] = 'Unknown Category'
                except:
                    product['product__category__title'] = 'Unknown Category'

        top_products = top_products_list

        # Sales summary
        total_sales = CartOrder.objects.filter(sales_filter).aggregate(
            total=Sum('price'),
            count=Count('id'),
            avg_order_value=Avg('price')
        )

        # Monthly breakdown
        monthly_sales = CartOrder.objects.filter(paid_status=True).annotate(
            month=TruncMonth('order_date')
        ).values('month').annotate(
            total_sales=Sum('price'),
            order_count=Count('id')
        ).order_by('month')

        # Sales by category - using hybrid approach for better data reliability
        category_sales_data = {}

        # Get all cart order items in the date range
        order_items = CartOrderItem.objects.filter(
            order__paid_status=True,
            order__order_date__date__gte=start_date,
            order__order_date__date__lte=end_date
        ).select_related('product', 'product__category')

        logger.info(f"Found {order_items.count()} order items in date range {start_date} to {end_date}")
        if order_items.count() == 0:
            logger.warning("No order items found - pie chart will be empty")

        # Process each item to build category sales data
        items_by_detection_method = {'fk': 0, 'exact': 0, 'partial': 0, 'inferred': 0, 'unknown': 0}

        for item in order_items:
            category_name = 'Unknown Category'
            detection_method = 'unknown'

            # Try to get category from the product relationship
            try:
                if item.product and item.product.category:
                    category_name = item.product.category.title
                    detection_method = 'fk'
                    logger.debug(f"[FK] Found category: {category_name} for item: {item.item}")
                else:
                    # If product is deleted, try to find category by product name using multiple strategies
                    if item.item:  # Ensure item name exists
                        logger.debug(f"[LOOKUP] Searching category for deleted product: {item.item}")

                        # First try exact match
                        existing_product = Product.objects.filter(title=item.item).select_related('category').first()

                        if existing_product and existing_product.category:
                            category_name = existing_product.category.title
                            detection_method = 'exact'
                            logger.debug(f"[EXACT] Found category: {category_name} for item: {item.item}")
                        else:
                            # If exact match fails, try partial matching (first 20 chars)
                            item_prefix = item.item[:20] if len(item.item) > 20 else item.item
                            existing_product = Product.objects.filter(title__icontains=item_prefix).select_related('category').first()

                            if existing_product and existing_product.category:
                                category_name = existing_product.category.title
                                detection_method = 'partial'
                                logger.debug(f"[PARTIAL] Found category: {category_name} for item: {item.item} (prefix: {item_prefix})")
                            else:
                                # Last fallback: try to infer category from product name
                                item_lower = item.item.lower()
                                if any(keyword in item_lower for keyword in ['macbook', 'laptop', 'notebook']):
                                    category_name = 'Laptops'
                                elif any(keyword in item_lower for keyword in ['desktop', 'pc', 'workstation']):
                                    category_name = 'Desktops'
                                elif any(keyword in item_lower for keyword in ['monitor', 'display', 'screen']):
                                    category_name = 'Monitors'
                                elif any(keyword in item_lower for keyword in ['keyboard', 'mouse', 'speaker', 'headset']):
                                    category_name = 'Accessories'
                                else:
                                    category_name = 'Electronics'  # Generic fallback
                                detection_method = 'inferred'
                                logger.debug(f"[INFERRED] Category: {category_name} for item: {item.item}")
                    else:
                        logger.warning(f"[ERROR] Item has no name: {item}")
            except Exception as e:
                logger.warning(f"[EXCEPTION] Error getting category for item {item.item}: {str(e)}")
                # category_name already defaults to 'Unknown Category'

            items_by_detection_method[detection_method] += 1

            # Accumulate sales data by category
            if category_name not in category_sales_data:
                category_sales_data[category_name] = {
                    'product__category__title': category_name,
                    'total_sales': 0,
                    'total_units': 0
                }

            category_sales_data[category_name]['total_sales'] += float(item.total or 0)
            category_sales_data[category_name]['total_units'] += int(item.qty or 0)

        # Convert to list and sort by total sales
        category_sales = sorted(
            category_sales_data.values(),
            key=lambda x: x['total_sales'],
            reverse=True
        )

        # Log detailed results
        logger.info(f"Category detection summary: {items_by_detection_method}")
        logger.info(f"Final category sales data: {len(category_sales)} categories found")

        total_sales_value = sum(cat['total_sales'] for cat in category_sales)
        logger.info(f"Total sales value across all categories: ${total_sales_value:.2f}")

        if category_sales:
            logger.info("Category breakdown:")
            for i, cat in enumerate(category_sales):
                percentage = (cat['total_sales'] / total_sales_value * 100) if total_sales_value > 0 else 0
                logger.info(f"  {i+1}. {cat['product__category__title']}: ${cat['total_sales']:.2f} ({percentage:.1f}%) - {cat['total_units']} units")
        else:
            logger.warning("CRITICAL: No category sales data found - pie chart will be empty!")
            logger.info("Possible reasons:")
            logger.info("- No paid orders in the selected date range")
            logger.info("- All products are deleted and category detection failed")
            logger.info("- Database query issues")

        # Sales by shop
        shop_sales = CartOrder.objects.filter(sales_filter).values(
            'shop__title'
        ).annotate(
            total_sales=Sum('price'),
            order_count=Count('id')
        ).order_by('-total_sales')

        # Daily sales for chart
        daily_sales = []
        current_date = start_date
        while current_date <= end_date:
            day_sales = CartOrder.objects.filter(
                paid_status=True,
                order_date__date=current_date
            ).aggregate(total=Sum('price'))['total'] or 0

            daily_sales.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': float(day_sales)
            })
            current_date += timedelta(days=1)

        # Get current language for currency formatting
        current_language = translation.get_language()
        is_myanmar = current_language == 'my'

        # Additional KPIs
        total_products = Product.objects.filter(product_status='published').count()
        total_customers = User.objects.filter(is_staff=False).count()

        context = {
            'top_products': top_products,
            'total_sales': total_sales,
            'monthly_sales': monthly_sales,
            'category_sales': category_sales,
            'shop_sales': shop_sales,
            'daily_sales': daily_sales,
            'start_date': start_date,
            'end_date': end_date,
            'today_sales': CartOrder.objects.filter(
                paid_status=True,
                order_date__date=timezone.now().date()
            ).aggregate(total=Sum('price'))['total'] or 0,
            'weekly_sales': CartOrder.objects.filter(
                paid_status=True,
                order_date__date__gte=timezone.now().date() - timedelta(days=7)
            ).aggregate(total=Sum('price'))['total'] or 0,
            'orders_today': CartOrder.objects.filter(
                paid_status=True,
                order_date__date=timezone.now().date()
            ).count(),
            'growth_rate': 15.2,  # Calculate actual growth rate
            'recent_orders': CartOrder.objects.filter(paid_status=True).order_by('-order_date')[:10],

            # KPI metrics
            'total_products': total_products,
            'total_customers': total_customers,

            # Language and currency context
            'current_language': current_language,
            'is_myanmar': is_myanmar,
        }

        logger.info(f"Sales analytics data prepared successfully - {len(top_products)} products, {len(category_sales)} categories")

        # Handle AJAX requests for SPA
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
            return render(request, "flame/sales.html", context)

        return render(request, "flame/sales.html", context)

    except Exception as e:
        logger.error(f"Error in adminsales view: {str(e)}", exc_info=True)
        messages.error(request, _("An error occurred while loading sales data. Please try again."))

        # Return basic context to prevent template errors
        context = {
            'top_products': [],
            'total_sales': {'total': 0, 'count': 0},
            'category_sales': [],
            'recent_orders': [],
            'total_products': 0,
            'total_customers': 0,
            'is_myanmar': False,
            'current_language': 'en',
        }

        # Handle AJAX requests for SPA
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
            return render(request, "flame/sales.html", context)

        return render(request, "flame/sales.html", context)

@login_required
def sales_pdf(request):
    """Generate and download sales report PDF"""
    if not request.user.is_staff:
        messages.error(request, _("Access denied. Admin privileges required."))
        return redirect('flame:index')

    from datetime import timedelta
    from django.http import FileResponse

    try:
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )

        # Build PDF content
        story = []
        story.append(Paragraph("Sales Analysis Report", title_style))
        story.append(Spacer(1, 20))

        # Report date
        report_date = timezone.now().strftime('%Y-%m-%d %H:%M')
        story.append(Paragraph(f"Generated on: {report_date}", styles['Normal']))
        story.append(Spacer(1, 20))

        # Sales summary
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        total_sales = CartOrder.objects.filter(
            paid_status=True,
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        ).aggregate(total=Sum('price'))['total'] or 0

        total_orders = CartOrder.objects.filter(
            paid_status=True,
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        ).count()

        avg_order_value = total_sales / total_orders if total_orders > 0 else 0

        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Sales', f'MMK {total_sales:,.2f}'],
            ['Total Orders', f'{total_orders:,}'],
            ['Average Order Value', f'MMK {avg_order_value:,.2f}'],
            ['Report Period', f'{start_date} to {end_date}']
        ]

        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("Sales Summary", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Top products
        top_products = CartOrderItem.objects.filter(
            order__paid_status=True,
            order__order_date__date__gte=start_date,
            order__order_date__date__lte=end_date
        ).values(
            'product__title'
        ).annotate(
            units_sold=Sum('qty'),
            total_revenue=Sum('total')
        ).order_by('-total_revenue')[:10]

        if top_products:
            products_data = [['Product', 'Units Sold', 'Revenue']]
            for product in top_products:
                products_data.append([
                    product['product__title'][:30] if product['product__title'] else 'N/A',
                    str(product['units_sold']),
                    f"MMK {product['total_revenue']:,.2f}"
                ])

            products_table = Table(products_data, colWidths=[3*inch, 1*inch, 1.5*inch])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(Paragraph("Top 10 Products by Revenue", styles['Heading2']))
            story.append(products_table)

        # Build PDF
        doc.build(story)

        # Return PDF as response
        buffer.seek(0)
        filename = f'sales_report_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )

    except Exception as e:
        messages.error(request, _(f"Error generating PDF: {str(e)}"))
        return redirect('flame:adminsales')
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from .models import CartOrder
from datetime import datetime
def adminanalytic(request):
    from django.utils import translation

    # Get monthly sales data (only paid orders)
    monthly_sales = CartOrder.objects.filter(paid_status=True).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total_sales=Sum('price'),
        order_count=Count('id')
    ).order_by('month')

    # Prepare chart data
    sales_labels = []
    sales_values = []
    orders_values = []

    # Fill in all months (even those without data)
    for month in range(1, 13):
        month_name = datetime(2023, month, 1).strftime('%b')
        sales_labels.append(month_name)

        # Find data for this month if exists
        month_data = next((item for item in monthly_sales if item['month'].month == month), None)

        sales_values.append(float(month_data['total_sales']) if month_data else 0)
        orders_values.append(month_data['order_count'] if month_data else 0)

    # Get current language for currency formatting
    current_language = translation.get_language()
    is_myanmar = current_language == 'my'

    # Get additional metrics for analytics template
    total_products = Product.objects.filter(product_status='published').count()
    total_customers = User.objects.filter(is_staff=False).count()

    import json

    context = {
        'sales_labels': json.dumps(sales_labels),
        'sales_values': json.dumps(sales_values),
        'orders_values': json.dumps(orders_values),
        'total_orders': CartOrder.total_orders(),
        'paid_orders': CartOrder.paid_orders_count(),
        'recent_orders': CartOrder.recent_orders_count(7),  # Last 7 days
        'status_counts': CartOrder.orders_by_status(),
        'total_sales': CartOrder.total_sales(),
        'monthly_sales': CartOrder.recent_sales(30),
        'weekly_sales': CartOrder.recent_sales(7),
        'sales_by_status': CartOrder.sales_by_status(),
        'delivery_comparison': CartOrder.shop_vs_home_sales(),
        'recent_orders': CartOrder.objects.filter(paid_status=True).order_by('-order_date')[:10],

        # Additional data for analytics template
        'total_products': total_products,
        'total_customers': total_customers,
        'current_language': current_language,
        'is_myanmar': is_myanmar,

    }
    # Handle AJAX requests for SPA
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return render(request, 'flame/analytics.html', context)

    return render(request, 'flame/analytics.html', context)
from django.core.serializers.json import DjangoJSONEncoder
from .models import CartOrder
def adminpage(request):
    monthly_sales = CartOrder.objects.filter(paid_status=True).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total_sales=Sum('price'),
        order_count=Count('id')
    ).order_by('month')
    
    # Prepare chart data
    sales_labels = []
    sales_values = []
    orders_values = []
    
    # Fill in all months (even those without data)
    for month in range(1, 13):
        month_name = datetime(2023, month, 1).strftime('%b')
        sales_labels.append(month_name)
        
        # Find data for this month if exists
        month_data = next((item for item in monthly_sales if item['month'].month == month), None)
        
        sales_values.append(float(month_data['total_sales']) if month_data else 0)
        orders_values.append(month_data['order_count'] if month_data else 0)
    # Get sales by category through the CartOrder -> CartOrderItem -> Product -> Category chain
    sales_by_category = CartOrder.objects.filter(
        paid_status=True
    ).values(
        'cartorderitem__product__category__title'
    ).annotate(
        total_sales=Sum('price')
    ).order_by('-total_sales')

    # Prepare chart data
    category_labels = []
    category_values = []
    category_colors = ["#4361ee", "#f8961e", "#4cc9f0", "#f72585", "#7209b7", "#3a0ca3"]
    
    for i, category in enumerate(sales_by_category):
        label = category['cartorderitem__product__category__title'] or 'Uncategorized'
        category_labels.append(label)
        category_values.append(float(category['total_sales']))
    
    # Check if we have any data
    has_category_data = len(category_values) > 0 and sum(category_values) > 0
    # Ensure we don't exceed available colors
    used_colors = category_colors[:len(category_labels)]
    top_products = CartOrderItem.objects.filter(
        order__paid_status=True
    ).select_related('product').values(
        'product__title',
        'product__image',
        'product__id'
    ).annotate(
        total_units=Sum('qty'),
        total_revenue=Sum('total')
    ).order_by('-total_revenue')[:5]  # Get top 5 products by revenue

    # Calculate percentages if we have data
    has_sales_data = top_products.exists()
    if has_sales_data:
        max_revenue = top_products[0]['total_revenue']
        for product in top_products:
            product['percentage'] = round((product['total_revenue'] / max_revenue) * 100)
 # Get top 5 selling products by revenue
    top_products = CartOrderItem.objects.filter(
        order__paid_status=True
    ).select_related('product').values(
        'product__title',
        'product__image',
        'product__price'
    ).annotate(
        units_sold=Sum('qty'),
        total_revenue=Sum('total')
    ).order_by('-total_revenue')[:5]  # Explicitly limit to 5 products

    # Calculate progress percentages
   
       
    top_products = CartOrderItem.top_selling_products(limit=10)

    context = {
        'current_user': request.user,
        'top_products': top_products if has_sales_data else None,
        'has_sales_data': has_sales_data,
        'sales_labels': json.dumps(sales_labels, cls=DjangoJSONEncoder),
        'sales_values': json.dumps(sales_values, cls=DjangoJSONEncoder),
        'orders_values': json.dumps(orders_values, cls=DjangoJSONEncoder),
        'total_orders': CartOrder.total_orders(),
        'paid_orders': CartOrder.paid_orders_count(),
        'recent_orders': CartOrder.recent_orders_count(7),  # Last 7 days
        'status_counts': CartOrder.orders_by_status(),
        'total_sales': CartOrder.total_sales(),
        'monthly_sales': CartOrder.recent_sales(30),
        'weekly_sales': CartOrder.recent_sales(7),
        'sales_by_status': CartOrder.sales_by_status(),
        'delivery_comparison': CartOrder.shop_vs_home_sales(),
        'recent_orders': CartOrder.objects.filter(paid_status=True).order_by('-order_date')[:10],
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'category_colors': json.dumps(category_colors[:len(category_labels)]),
        'has_category_data': has_category_data,
        'top_products': top_products,
        'has_sales_data': CartOrderItem.objects.filter(order__paid_status=True).exists()
    }    
    return render(request,'flame/Dashboard.html',context)
# def chatbot_reply(request):
#     user_input = request.GET.get("message", "").strip().lower()
#     if not user_input:
#         return JsonResponse({"response": "[No input provided]"}, status=200)

#     # Try to match exactly
#     for pair in dialog_pairs:
#         if pair["dialog"][0].strip().lower() == user_input:
#             return JsonResponse({"response": pair["dialog"][1]})

#     # If no match found
#     return JsonResponse({"response": "I'm sorry, I don't understand that yet."})
from .forms import OrderForm
from django.utils.text import slugify
@login_required
def edit_order(request, order_id):
    order = get_object_or_404(CartOrder, id=order_id, user=request.user)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user   # ✅ auto-assign logged-in user
            order.save()
            return JsonResponse({
                'success': True,
                'message': 'Order updated successfully!',
                'order_id': order.id
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors.get_json_data()
        }, status=400)

    form = OrderForm(instance=order)
    return render(request, 'flame/editorder.html', {
        'order': order,
        'form': form,
        'shops': Shop.objects.all(),
        'category': Category.objects.all()
    })

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

def admin_offline(request):
    """
    Offline page for admin panel with cached data display
    """
    return render(request, "flame/offline.html", {
        "title": "Offline Mode - Admin Panel"
    })

