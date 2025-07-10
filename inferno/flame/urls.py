# flame/urls.py
from django.urls import path, include
from . import views

app_name = 'flame'  # This is essential to register the namespace

urlpatterns = [
    # Homepage
    path("", views.home, name= "home"),
    path("products/",views.product_list_view,name="product-list"), # Product List View Path
    path("shop/<str:sid>/products/",views.shop_product_list_view, name="shop-product-list"), # Product List View With Respect to Shop Path
    path("shop/<str:sid>/product/<str:pid>/",views.shop_product_detail_view, name="shop-product-detail"), # Product Detail View Path
    
    
    path("product/<pid>/",views.product_detail_view,name="product-detail"),
    
    # Category
    path("category/",views.category_list_view,name="category-list"),
    path("category/<cid>/",views.category_product_list_view,name="category-product-list"),
    
    # Brands
    path("brand/<bid>/",views.brand_product_list_view,name="brand-product-list"),
    
    # Shop
    path("shop/", views.shop_list_view, name="shop-list"), # shop list path
    path("shop/<str:sid>/", views.shop_detail_view, name= "shop-detail"), # shop list detail view path
    
    #Tags
    #here will be tag list URLS
    
    #Add Review
    path("ajax-add-review/<int:pid>/", views.ajax_add_review, name= "ajax_add_review"),
    
    # Search 
    path("search/", views.search_view ,name="search"),
    
    # Filter Home Products
    path("filter-products/", views.filter_product, name="filter-product"),

    
   
    
    # Cart Page
    path("shop-cart/",views.shop_cart_view, name="shop-cart"), # cart url
    path("add-to-shop-cart/", views.add_to_shop_cart, name="add-to-shop-cart"), # add to cart url
    path("delete-from-shop-cart", views.delete_item_from_shop_cart, name="delete-from-shop-cart"), # delete from cart url
    path("update-shop-cart", views.update_shop_cart, name="update-shop-cart"),   # path("cart/",views.cart_view, name="cart"),
    # path("add-to-cart/",views.add_to_cart, name="add-to-cart"),
    # path("delete-from-cart/",views.delete_item_from_cart, name="delete-from-cart"),
    # path("update-cart/",views.update_cart, name="update-cart"),
    
    
    # Check out 
    path('checkout/shop/<str:sid>/', views.shop_checkout_view, name='shop-checkout'),
    # path("checkout/home/", views.home_checkout_view, name="home-checkout"),
    
    # Paypal
    path("paypal/", include('paypal.standard.ipn.urls')),
    
    # Payment Success Url
    path('payment-completed/<str:sid>/', views.shop_payment_completed_view, name='payment-completed'),
    # path('payment-completed/',views.payment_completed_view,name='payment-completed'),
    
    # Payment Fail Url
    path('payment-failed/',views.payment_failed_view,name='payment-failed'),
    
    # Customer Profile
    path('profile/',views.customer_profile,name='profile'),
    
    # Order Details
    path('profile/order/<int:id>',views.order_detail,name='order-detail'),
    
    # Making Default Address
    path('make-default-address/',views.make_address_default,name='make-default-address'),
    
    # Wishlist Url
    path('wishlist/',views.wishlist_view,name='wishlist'),
    
    # Adding wishlist 
    path("add-to-wishlist/",views.add_to_wishlist, name="add-to-wishlist"),
    
    # Delete from wishlist
    path("remove-from-wishlist/",views.remove_from_wishlist, name="remove-from-wishlist"),
    
    # Stripe Payment Integration
    path('api/create-checkout-session/<str:sid>/', views.create_checkout_session, name='create-checkout-session'),
    path('stripe-payment-completed/<str:sid>/', views.stripe_payment_completed_view, name='stripe-payment-completed'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe-webhook'),
    
    #FAQs
    path("FAQs/", views.FAQs, name= "FAQs"),
    
      #FAQs
    path("FAQs/", views.FAQs, name= "FAQs"),
    
    # About 
    path("About/", views.About, name= "About"),
    
    # About Us
    path("About-Us/", views.AboutUs, name= "AboutUs"),
    
    # Service
    path("Services/", views.Services, name= "Services"),
    
    # Privacy Policy
    path("Privacy-Policy/", views.PrivacyPolicy, name= "PrivacyPolicy"),
    
    # Terms and Conditions
    path("Terms-and-Conditions/", views.Terms, name= "Terms"),
    
    # Return Policy
    path("Return-Policy/", views.ReturnPolicy, name= "ReturnPolicy"),
    
]
