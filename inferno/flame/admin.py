from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from flame.models import (
    Brand, Product, Category, Shop, ExchangeRate,
    CartOrder, CartOrderItem, ProductImages,
    ProductReview, Wishlist, Address
)
from flame.utils.myanmar_utils import update_exchange_rates_from_api
from django.utils.html import format_html

User = get_user_model()

# ----- safe unregister helpers -----
def safe_unregister(model):
    try:
        if model in admin.site._registry:
            admin.site.unregister(model)
    except Exception:
        # defensive: ignore problems here (rare)
        pass

# Unregister if already registered (safe)
for m in (Product, Category, Brand, Shop):
    safe_unregister(m)


# ----- admin classes -----
class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages
    
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['currency_from', 'currency_to', 'rate', 'markup_percentage', 
                    'effective_rate_display', 'is_active', 'last_updated']
    list_filter = ['is_active', 'last_updated']
    readonly_fields = ['last_updated', 'updated_by']
    
    def effective_rate_display(self, obj):
        rate = obj.get_effective_rate()
        # Ensure rate is a numeric type before formatting
        try:
            numeric_rate = float(rate)
            return format_html('<strong>{:.2f}</strong>', numeric_rate)
        except (TypeError, ValueError):
            return format_html('<strong>{}</strong>', rate)  # Fallback for non-numeric values
    effective_rate_display.short_description = 'Effective Rate'
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        # Clear cache when rate is updated
        from django.core.cache import cache
        cache.delete(f'exchange_rate_{obj.currency_from}_{obj.currency_to}')
    
    actions = ['update_rates_from_api']
    
    def update_rates_from_api(self, request, queryset):
        if update_exchange_rates_from_api():
            self.message_user(request, "Exchange rates updated successfully!")
        else:
            self.message_user(request, "Failed to update exchange rates. Check logs.", level=messages.ERROR)
    update_rates_from_api.short_description = "Update rates from API"

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ['user', 'title', 'product_image', 'price',  'price_usd_display', 'price_mmk_display', 'shop', 'category', 'brand', 'featured', 'product_status', 'p_id']
    # If you use django-modeltranslation fields, keep these search_fields; else revert to title/description
    search_fields = ['title_en', 'title_my', 'description_en', 'description_my']

    def price_usd_display(self, obj):
        return f"${obj.price:,.2f}"
    price_usd_display.short_description = 'Price (USD)'
    
    def price_mmk_display(self, obj):
        from flame.utils.myanmar_utils import format_myanmar_currency
        mmk_price = obj.get_price_mmk()
        return format_myanmar_currency(mmk_price)
    price_mmk_display.short_description = 'Price (MMK)'
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(shop__user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and 'shop' in form.base_fields:
            del form.base_fields['shop']
        return form

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            # assign the first shop of the user (your previous behavior)
            obj.shop = request.user.shops.first()
        super().save_model(request, obj, form, change)


class BrandAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand_image_display']
    search_fields = ['title_en', 'title_my']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_image']
    search_fields = ['title_en', 'title_my']

class ShopAdmin(admin.ModelAdmin):
    list_display = ['title', 'shop_image', 'user']
    search_fields = ['title_en', 'title_my', 'description_en', 'description_my']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser


class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ['paid_status', 'product_status']
    list_display = ['user', 'price', 'paid_status', 'order_date', 'product_status']

class CartOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'invoice_no', 'product_status', 'item', 'image', 'qty', 'price', 'total']

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review', 'rating']

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date']

class AddressAdmin(admin.ModelAdmin):
    list_editable = ['address', 'status']
    list_display = ['user', 'address', 'status']


# ----- register models -----
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
