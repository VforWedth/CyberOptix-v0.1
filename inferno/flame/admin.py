from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from flame.models import (
    Brand, Product, Category, Shop, ExchangeRate,
    CartOrder, CartOrderItem, ProductImages,
    ProductReview, Wishlist, Address,
    InventoryLog, SupplierContact, SupplierProduct,
    OrderStatusHistory, ReviewHelpful, ReviewImage, ReviewReport,
    UserBehavior, ProductSimilarity, RecommendationList, RecommendationItem,
    ProductAnalytics, SalesAnalytics, CustomerAnalytics,
    EmailTemplate, EmailLog,
    SocialMediaAccount, SocialMediaPost,
    MyanmarState, MyanmarCity, MyanmarTownship, ShippingRate
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
# ================================ INVENTORY MANAGEMENT ================================

class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'action', 'quantity', 'cost_per_unit', 'user', 'timestamp', 'stock_after']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['product__title', 'notes']
    readonly_fields = ['timestamp', 'stock_after', 'reserved_after']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

class SupplierProductInline(admin.TabularInline):
    model = SupplierProduct
    extra = 1

class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'company', 'email']
    inlines = [SupplierProductInline]

class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'product', 'supplier_sku', 'cost_price', 'minimum_order_quantity', 'lead_time_days', 'is_preferred']
    list_filter = ['is_preferred', 'lead_time_days']
    search_fields = ['supplier__name', 'product__title', 'supplier_sku']

# ================================ ORDER TRACKING ================================

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['timestamp']

class EnhancedCartOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'payment_method', 'product_status', 'order_date', 'tracking_number', 'progress_bar']
    list_filter = ['product_status', 'order_date', 'paid_status', 'payment_method']
    search_fields = ['order_number', 'user__username', 'tracking_number']
    inlines = [OrderStatusHistoryInline]
    readonly_fields = ['order_number', 'order_date']
    date_hierarchy = 'order_date'
    
    def progress_bar(self, obj):
        progress = obj.get_order_progress()
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: #4CAF50; height: 20px; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
            '{}%</div></div>',
            progress, progress
        )
    progress_bar.short_description = 'Progress'

class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'timestamp', 'location', 'carrier']
    list_filter = ['status', 'timestamp', 'carrier']
    search_fields = ['order__order_number', 'notes', 'location']
    date_hierarchy = 'timestamp'

# ================================ REVIEWS & RATINGS ================================

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1

class ReviewHelpfulInline(admin.TabularInline):
    model = ReviewHelpful
    extra = 0
    readonly_fields = ['created_at']

class EnhancedProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'title', 'rating', 'quality_rating', 'is_verified_purchase', 'is_approved', 'helpful_count', 'date']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'is_featured', 'date']
    search_fields = ['user__username', 'product__title', 'title', 'review']
    inlines = [ReviewImageInline, ReviewHelpfulInline]
    readonly_fields = ['date', 'updated_at']
    actions = ['approve_reviews', 'feature_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews were approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} reviews were featured.')
    feature_reviews.short_description = "Feature selected reviews"

class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['user__username', 'review__title']

class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['review__title', 'caption']

class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['review', 'reported_by', 'reason', 'is_resolved', 'created_at']
    list_filter = ['reason', 'is_resolved', 'created_at']
    search_fields = ['review__title', 'reported_by__username', 'description']
    actions = ['resolve_reports']
    
    def resolve_reports(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} reports were resolved.')
    resolve_reports.short_description = "Resolve selected reports"

# ================================ RECOMMENDATION ENGINE ================================

class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'product', 'score', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'product__title', 'search_query']
    date_hierarchy = 'timestamp'

class ProductSimilarityAdmin(admin.ModelAdmin):
    list_display = ['product_1', 'product_2', 'similarity_score', 'last_calculated']
    list_filter = ['similarity_score', 'last_calculated']
    search_fields = ['product_1__title', 'product_2__title']
    ordering = ['-similarity_score']

class RecommendationItemInline(admin.TabularInline):
    model = RecommendationItem
    extra = 0
    ordering = ['rank']

class RecommendationListAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'based_on_product', 'created_at', 'expires_at', 'is_active']
    list_filter = ['recommendation_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'based_on_product__title']
    inlines = [RecommendationItemInline]
    date_hierarchy = 'created_at'

class RecommendationItemAdmin(admin.ModelAdmin):
    list_display = ['recommendation_list', 'product', 'rank', 'score', 'reason']
    list_filter = ['rank', 'score']
    search_fields = ['product__title', 'reason']

# ================================ ANALYTICS & REPORTING ================================

class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['product', 'date', 'views', 'unique_views', 'cart_adds', 'purchases', 'revenue', 'view_to_cart_rate']
    list_filter = ['date']
    search_fields = ['product__title']
    date_hierarchy = 'date'
    readonly_fields = ['view_to_cart_rate', 'cart_to_purchase_rate']

class SalesAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'total_items_sold', 'new_customers', 'average_order_value']
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['date']

class CustomerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'segment', 'total_orders', 'total_spent', 'average_order_value', 'last_purchase_date']
    list_filter = ['segment', 'preferred_category', 'preferred_brand']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']
    actions = ['update_segments']
    
    def update_segments(self, request, queryset):
        for analytics in queryset:
            analytics.update_segment()
        self.message_user(request, f'Updated segments for {queryset.count()} customers.')
    update_segments.short_description = "Update customer segments"

# ================================ EMAIL NOTIFICATIONS ================================

class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['email_type', 'is_active', 'updated_at']
    search_fields = ['name', 'subject']

class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'email_type', 'subject', 'status', 'sent_at', 'opened_at']
    list_filter = ['email_type', 'status', 'sent_at']
    search_fields = ['recipient_email', 'subject', 'user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at']

# ================================ SOCIAL MEDIA INTEGRATION ================================

class SocialMediaPostInline(admin.TabularInline):
    model = SocialMediaPost
    extra = 1
    fields = ['content', 'status', 'scheduled_at']

class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ['platform', 'account_name', 'is_active', 'is_auto_post', 'updated_at']
    list_filter = ['platform', 'is_active', 'is_auto_post']
    search_fields = ['account_name', 'account_url']
    inlines = [SocialMediaPostInline]

class SocialMediaPostAdmin(admin.ModelAdmin):
    list_display = ['account', 'product', 'content_preview', 'status', 'published_at', 'likes', 'comments', 'shares']
    list_filter = ['status', 'account__platform', 'published_at']
    search_fields = ['content', 'product__title']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

# ================================ ENHANCED PRODUCT ADMIN ================================

class EnhancedProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ['title', 'product_image', 'price_usd_display', 'price_mmk_display', 'stock_status', 'available_stock', 'category', 'brand', 'featured', 'product_status']
    list_filter = ['category', 'brand', 'featured', 'product_status', 'in_stock']
    search_fields = ['title', 'description', 'sku']
    readonly_fields = ['sku', 'date', 'updated']
    actions = ['mark_featured', 'restock_products', 'generate_low_stock_report']
    
    def stock_status(self, obj):
        available = obj.get_available_stock()
        if obj.is_out_of_stock():
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.is_low_stock():
            return format_html('<span style="color: orange;">Low Stock ({}/{})</span>', available, obj.stock_count)
        else:
            return format_html('<span style="color: green;">In Stock ({}/{})</span>', available, obj.stock_count)
    stock_status.short_description = 'Stock Status'
    
    def available_stock(self, obj):
        return f"{obj.get_available_stock()} available"
    available_stock.short_description = 'Available Stock'
    
    def price_usd_display(self, obj):
        return f"${obj.price:,.2f}"
    price_usd_display.short_description = 'Price (USD)'
    
    def price_mmk_display(self, obj):
        from flame.utils.myanmar_utils import format_myanmar_currency
        mmk_price = obj.get_price_mmk()
        return format_myanmar_currency(mmk_price)
    price_mmk_display.short_description = 'Price (MMK)'
    
    def mark_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} products were marked as featured.')
    mark_featured.short_description = "Mark selected products as featured"
    
    def restock_products(self, request, queryset):
        # This would typically redirect to a form for bulk restocking
        self.message_user(request, "Use the inventory management system for restocking.")
    restock_products.short_description = "Restock selected products"
    
    def generate_low_stock_report(self, request, queryset):
        low_stock_products = [p for p in queryset if p.is_low_stock()]
        if low_stock_products:
            self.message_user(request, f'Found {len(low_stock_products)} products with low stock.')
        else:
            self.message_user(request, 'No low stock products found.')
    generate_low_stock_report.short_description = "Generate low stock report"

# ================================ MYANMAR LOCATION ADMIN ================================

@admin.register(MyanmarState)
class MyanmarStateAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_mm', 'code', 'cities_count']
    list_filter = ['code']
    search_fields = ['name', 'name_mm', 'code']
    ordering = ['name']

    def cities_count(self, obj):
        return obj.cities.count()
    cities_count.short_description = 'Cities Count'

@admin.register(MyanmarCity)
class MyanmarCityAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_mm', 'state', 'is_major_city', 'townships_count']
    list_filter = ['state', 'is_major_city']
    search_fields = ['name', 'name_mm', 'state__name']
    ordering = ['state__name', 'name']

    def townships_count(self, obj):
        return obj.townships.count()
    townships_count.short_description = 'Townships Count'

@admin.register(MyanmarTownship)
class MyanmarTownshipAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_mm', 'city', 'state_name']
    list_filter = ['city__state', 'city']
    search_fields = ['name', 'name_mm', 'city__name', 'city__state__name']
    ordering = ['city__state__name', 'city__name', 'name']

    def state_name(self, obj):
        return obj.city.state.name
    state_name.short_description = 'State'

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['shop', 'from_location', 'to_location', 'rate_mmk_display', 'rate_usd_display', 'is_same_city', 'is_same_state']
    list_filter = ['shop', 'from_state', 'to_state', 'is_same_city', 'is_same_state']
    search_fields = ['shop__title', 'from_city__name', 'to_city__name']
    ordering = ['shop', 'from_state', 'from_city', 'to_city']

    def from_location(self, obj):
        return f"{obj.from_city.name}, {obj.from_state.name}"
    from_location.short_description = 'From'

    def to_location(self, obj):
        return f"{obj.to_city.name}, {obj.to_state.name}"
    to_location.short_description = 'To'

    def rate_mmk_display(self, obj):
        return f"{obj.rate_mmk:,.0f} MMK"
    rate_mmk_display.short_description = 'Rate (MMK)'

    def rate_usd_display(self, obj):
        return f"${obj.rate_usd:.2f}"
    rate_usd_display.short_description = 'Rate (USD)'

# ================================ REGISTER ALL MODELS ================================

# Basic models
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Address, AddressAdmin)

# Enhanced models
admin.site.register(Product, EnhancedProductAdmin)
admin.site.register(CartOrder, EnhancedCartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(ProductReview, EnhancedProductReviewAdmin)

# Inventory Management
admin.site.register(InventoryLog, InventoryLogAdmin)
admin.site.register(SupplierContact, SupplierContactAdmin)
admin.site.register(SupplierProduct, SupplierProductAdmin)

# Order Tracking
admin.site.register(OrderStatusHistory, OrderStatusHistoryAdmin)

# Reviews & Ratings
admin.site.register(ReviewHelpful, ReviewHelpfulAdmin)
admin.site.register(ReviewImage, ReviewImageAdmin)
admin.site.register(ReviewReport, ReviewReportAdmin)

# Recommendation Engine
admin.site.register(UserBehavior, UserBehaviorAdmin)
admin.site.register(ProductSimilarity, ProductSimilarityAdmin)
admin.site.register(RecommendationList, RecommendationListAdmin)
admin.site.register(RecommendationItem, RecommendationItemAdmin)

# Analytics & Reporting
admin.site.register(ProductAnalytics, ProductAnalyticsAdmin)
admin.site.register(SalesAnalytics, SalesAnalyticsAdmin)
admin.site.register(CustomerAnalytics, CustomerAnalyticsAdmin)

# Email Notifications
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailLog, EmailLogAdmin)

# Social Media Integration
admin.site.register(SocialMediaAccount, SocialMediaAccountAdmin)
admin.site.register(SocialMediaPost, SocialMediaPostAdmin)
