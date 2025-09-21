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
    
    # Reviews
    path("ajax-add-review/<int:pid>/", views.ajax_add_review, name="ajax_add_review"),
    path("enhanced-add-review/<int:pid>/", views.enhanced_add_review, name="enhanced-add-review"),
    path("mark-review-helpful/<int:review_id>/", views.mark_review_helpful, name="mark-review-helpful"),
    path("report-review/<int:review_id>/", views.report_review, name="report-review"),
    path("api/product/<int:product_id>/reviews/", views.product_reviews_api, name="product-reviews-api"),
    
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
    
    # API URLs (moved to main urls.py to avoid i18n prefix issues)
    
    # Check out
    path('checkout/shop/<str:sid>/', views.shop_checkout_view, name='shop-checkout'),
    path('checkout/direct/<str:sid>/', views.shop_checkout_direct_view, name='shop-checkout-direct'),
    # path("checkout/home/", views.home_checkout_view, name="home-checkout"),
    
    # Cash on Delivery Payment
    path('cod-payment/<str:sid>/', views.cod_payment_view, name='cod-payment'),
    
    # Paypal
    path("paypal/", include('paypal.standard.ipn.urls')),

    # Payment Success Url
    path('payment-completed/<str:sid>/', views.shop_payment_completed_view, name='payment-completed'),
    # path('payment-completed/',views.payment_completed_view,name='payment-completed'),
    
    # Payment Fail Url
    path('payment-failed/',views.payment_failed_view,name='payment-failed'),
    
    # Customer Profile
    path('profile/',views.customer_profile,name='profile'),

    # Shop Profile Management
    path('shop/<str:shop_id>/profile/', views.shop_profile_view, name='shop-profile'),
    path('shop/<str:shop_id>/update-location/', views.update_shop_location, name='update-shop-location'),
    path('shop/<str:shop_id>/manage-shipping/', views.manage_shipping_rates, name='manage-shipping-rates'),
    
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
    path('api/stripe-session-status/', views.stripe_session_status, name='stripe-session-status'),

    
    # KBZPay Payment Integration (moved to main urls.py outside i18n)
    
    
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
    path("Return-Policy/", views.ReturnPolicy, name="ReturnPolicy"),
    
    # ================================ ORDER TRACKING & MANAGEMENT ================================
    
    # Order Management
    path("orders/", views.order_list_view, name="order-list"),
    path("orders/<str:order_number>/", views.order_detail_view, name="order-detail"),
    path("orders/<str:order_number>/track/", views.track_order_view, name="track-order"),
    path("orders/<str:order_number>/cancel/", views.cancel_order_view, name="cancel-order"),
    path("orders/<str:order_number>/return/", views.return_order_view, name="return-order"),
    
    # Order API
    path("api/orders/<str:order_number>/status/", views.order_status_api, name="order-status-api"),
    
    # ================================ RECOMMENDATION SYSTEM ================================
    
    # Recommendations
    path("recommendations/", views.user_recommendations_view, name="user-recommendations"),
    path("api/product/<int:product_id>/recommendations/", views.product_recommendations_api, name="product-recommendations-api"),
    
    # ================================ ANALYTICS & REPORTING ================================
    
    # Analytics Dashboards
    path("admin/analytics/", views.analytics_dashboard_view, name="analytics-dashboard"),
    path("admin/analytics/product/<int:product_id>/", views.product_analytics_view, name="product-analytics"),
    path("admin/inventory/", views.inventory_dashboard_view, name="inventory-dashboard"),
    path("admin/inventory/bulk-restock/", views.bulk_restock_view, name="bulk-restock"),
    
    # Analytics API
    path("api/sales-report/", views.sales_report_api, name="sales-report-api"),
    
    # ================================ EMAIL MANAGEMENT ================================
    
    # Email Management
    path("email/preferences/", views.email_preferences_view, name="email-preferences"),
    path("unsubscribe/<int:user_id>/", views.email_unsubscribe_view, name="email-unsubscribe"),

    # ================================ OFFLINE FUNCTIONALITY ================================

    # Offline page
    # path("offline/", views.offline_view, name="offline"),

    # API endpoints for offline functionality
    path("api/ping/", views.api_ping, name="api-ping"),
    path("api/force-offline/", views.force_offline_mode, name="force-offline"),
    path("api/force-online/", views.force_online_mode, name="force-online"),
     path('chatbot/', views.chat_page,name="chatbot"),

    path('chatbot-reply/', views.chatbot_reply,name="chatbotReply"),

    path('admin-page-panel/',views.adminpage,name="adminpage"),
    path('admin-dashboard/',views.admindashboard,name="admindashboard"),
    path('admin-sales/',views.adminsales,name="adminsales"),
    path('admin-analytic/',views.adminanalytic,name="adminanalytic"),
    path('admin-dash/',views.admindash,name="admindash"),
    path('admin-noti/',views.adminnoti,name="adminnoti"),
    path('admin-security/',views.adminsecurity,name="adminsecurity"),
    path('admin-setting/',views.adminsetting,name="adminsetting"),

    path("orders/", views.orders, name="orders"),
    path("recommendation_page/",views.recommendation_page,name="recommendation_page"),
    path("adminproducts/", views.products, name="adminproducts"),

]
