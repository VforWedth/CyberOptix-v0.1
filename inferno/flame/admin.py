from django.contrib import admin
from flame.models import Brand, Product, Category, Shop, CartOrder, CartOrderItem, ProductImages, ProductReview , Wishlist, Address
from django.contrib.auth import get_user_model


User = get_user_model()

# Register your models here.
class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages
    
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    # list_filter = ('shop', 'product_type', 'brand')
    list_display = ['user', 'title', 'product_image', 'price', 'shop','category','brand','featured', 'product_status','p_id']
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(shop__user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'shop' in form.base_fields:
                del form.base_fields['shop']
        return form

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.shop = request.user.shops.first()
        super().save_model(request, obj, form, change)
    
class BrandAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand_image_display']
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category_image']
    
class ShopAdmin(admin.ModelAdmin):
    list_display = ['title', 'shop_image','user']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def has_add_permission(self, request):
        return request.user.is_superuser
    # prepopulated_fields = {'slug': ('title',)}
    
class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ['paid_status', 'product_status']
    list_display = ['user', 'price','paid_status','order_date','product_status']
    
class CartOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'invoice_no','product_status','item','image','qty', 'price', 'total' ]
  
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review','rating']
    
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'date']
    
class AdressAdmin(admin.ModelAdmin):
    list_editable = ['address', 'status']
    list_display = ['user', 'address', 'status']
    
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
# admin.site.register(ProductImages, ProductImagesAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Address, AdressAdmin)
# admin.site.unregister(Shop)
# admin.site.register(Shop,ShopAdmin)