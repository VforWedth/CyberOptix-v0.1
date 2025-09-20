"""
URL configuration for inferno project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# For Internationalization & Translation
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog

from django.conf import settings
from django.conf.urls.static import static

from flame.views import home
from flame.kbzpay_integration import initiate_kbzpay_payment, kbzpay_callback, check_payment_status
from flame import views as flame_views
from flame.paypal_dynamic import create_paypal_payment_with_shipping



urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('rosetta/', include('rosetta.urls')),  # Translation interface
    
    # PWA URLs
    path('', include('pwa.urls')),

    # API URLs (outside i18n_patterns for consistent API access)
    path('api/', include('api.urls')),

    # Flame API endpoints (outside i18n to avoid language prefix issues)
    path("api/format-price/", flame_views.format_price_api, name="format-price-api"),
    path("api/states/", flame_views.get_states_api, name="states-api"),
    path("api/cities-by-state/", flame_views.get_cities_by_state_api, name="cities-by-state-api"),
    path("api/townships-by-city/", flame_views.get_townships_by_city_api, name="townships-by-city-api"),
    path("api/calculate-shipping/", flame_views.calculate_shipping_fee_api, name="calculate-shipping-api"),
    path("api/store-checkout-address/", flame_views.store_checkout_address_api, name="store-checkout-address-api"),

    # PayPal Payment (outside i18n to avoid language prefix issues)
    path('api/create-paypal-payment/<str:sid>/', create_paypal_payment_with_shipping, name='create-paypal-payment'),

    # KBZPay Mock Payment Gateway (outside i18n for consistency)
    path('kbzpay/', include('kbzpay_mock.urls')),

    # KBZPay Integration URLs (outside i18n to avoid language prefix issues)
    path('payment/kbzpay/initiate/<int:order_id>/', initiate_kbzpay_payment, name='initiate_kbzpay'),
    path('payment/kbzpay/callback/', kbzpay_callback, name='kbzpay_callback'),
    path('payment/kbzpay/status/<int:order_id>/', check_payment_status, name='check_kbzpay_status'),

    # path('innwa/',include("innwaShop.urls")),
    # path('unique/',include("unique.urls")),
    # path('citicom/',include("citicomshop.urls")),
    # path('ict/',include("ict.urls")),
    # path('categories/',include("flame.urls")),
    # path('productdetails/',include("flame.urls")),
    # path('homeproductdetails/',include("flame.urls"))
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    
    path('', include("flame.urls")),
    path('user/', include("userauths.urls")),
    prefix_default_language= True,  # Don't show /en/ for default language
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)