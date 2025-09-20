from django.db import models
from django.db.models import JSONField
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from django.utils.text import slugify
from django.core.cache import cache
from decimal import Decimal
from django.utils import translation
from django.utils import timezone
from django.conf import settings
import logging

STATUS_CHOICE = (
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("processing", "Processing"),
    ("packed", "Packed"),
    ("shipped", "Shipped"),
    ("out_for_delivery", "Out for Delivery"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ("returned", "Returned"),
    ("refunded", "Refunded"),
)

STATUS = (
    ("draft","Draft"),
    ("disabled","Disabled"),
    ("rejected","Rejected"),
    ("in_review","In Review"),
    ("published","Published"),
)


RATING = (
    (1,"★☆☆☆☆"),
    (2,"★★☆☆☆"),
    (3,"★★★☆☆"),
    (4,"★★★★☆"),
    (5,"★★★★★"),
)

def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

#################################### Myanmar Location System ##########################
#################################### Myanmar Location System ##########################
#################################### Myanmar Location System ##########################

class MyanmarState(models.Model):
    """Myanmar States/Regions"""
    name = models.CharField(max_length=100)
    name_mm = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = "Myanmar States"
        ordering = ['name']

    def __str__(self):
        return self.name

class MyanmarCity(models.Model):
    """Myanmar Cities/Towns"""
    state = models.ForeignKey(MyanmarState, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    name_mm = models.CharField(max_length=100, blank=True)
    is_major_city = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Myanmar Cities"
        ordering = ['state__name', 'name']
        unique_together = ['state', 'name']

    def __str__(self):
        return f"{self.name}, {self.state.name}"

class MyanmarTownship(models.Model):
    """Myanmar Townships"""
    city = models.ForeignKey(MyanmarCity, on_delete=models.CASCADE, related_name='townships')
    name = models.CharField(max_length=100)
    name_mm = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "Myanmar Townships"
        ordering = ['city__name', 'name']
        unique_together = ['city', 'name']

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class ShippingRate(models.Model):
    """Shipping rates between different locations for shops"""
    # Note: Shop model will be defined later, so we'll use string reference
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='shipping_rates')
    from_state = models.ForeignKey(MyanmarState, on_delete=models.CASCADE, related_name='shipping_from')
    from_city = models.ForeignKey(MyanmarCity, on_delete=models.CASCADE, related_name='shipping_from_city')
    to_state = models.ForeignKey(MyanmarState, on_delete=models.CASCADE, related_name='shipping_to')
    to_city = models.ForeignKey(MyanmarCity, on_delete=models.CASCADE, related_name='shipping_to_city')

    rate_mmk = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rate_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_same_city = models.BooleanField(default=False)
    is_same_state = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shipping Rates"
        unique_together = ['shop', 'from_city', 'to_city']

    def save(self, *args, **kwargs):
        self.is_same_city = (self.from_city == self.to_city)
        self.is_same_state = (self.from_state == self.to_state)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shop.title}: {self.from_city} → {self.to_city} ({self.rate_mmk} MMK)"

#################################### Category, Product, Brand, Shop ##########################
#################################### Category, Product, Brand, Shop ##########################
#################################### Category, Product, Brand, Shop ##########################
# Create your models here.
class Category(models.Model):
    c_id =  ShortUUIDField(unique=True, length=10, max_length=20, prefix="cat", alphabet="abcdefghi12345")
    title = models.CharField(max_length=100, default="Laptops") 
    # Add JSON translation field
    title_translations = JSONField(default=dict, blank=True, help_text="Auto-translated titles")

    image = models.ImageField(upload_to="category", default="category.jpg")
    
    class Meta:
        verbose_name_plural = "Categories"
        
    def get_translated_title(self, language_code='en'):
        """Get title in specified language"""
        if language_code == 'en' or not self.title_translations:
            return self.title
        return self.title_translations.get(language_code, self.title)
        
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' %(self.image.url))
    
    def __str__(self):
        return self.title
    
class Tags(models.Model):
    pass
    
class Shop(models.Model):
    shop_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="shop", alphabet="abcdefghi12345")
    paypal_email = models.EmailField(default="lorendrain47@gmail.com")
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)
    title = models.CharField(max_length=100, default="Citicom")
    
    # JSON translation fields
    title_translations = JSONField(default=dict, blank=True)
    description_translations = JSONField(default=dict, blank=True)
    
    image = models.ImageField(upload_to=user_directory_path, default="shop.jpg")
    description = models.TextField(null=True, blank=True, default="Citicom Laptop Sale")
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops', null=True, blank=True)
    
    address = models.CharField(max_length=100, default="123 Rose Street.")
    contact = models.CharField(max_length=100, default="+959 123 456 789")
    chat_resp_time = models.CharField(max_length=100, default="100")
    shipping_on_time = models.CharField(max_length=100, default="100")
    authentic_rating = models.CharField(max_length=100, default="100")
    days_return = models.CharField(max_length=100, default="100")
    warranty_period = models.CharField(max_length=100, default="100")

    # Shop location fields
    state = models.ForeignKey(MyanmarState, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(MyanmarCity, on_delete=models.SET_NULL, null=True, blank=True)
    township = models.ForeignKey(MyanmarTownship, on_delete=models.SET_NULL, null=True, blank=True)
    street_address = models.CharField(max_length=200, null=True, blank=True, help_text="Street No, Building, etc.")

    def get_translated_title(self, language_code='en'):
        if language_code == 'en' or not self.title_translations:
            return self.title
        return self.title_translations.get(language_code, self.title)
    
    def get_translated_description(self, language_code='en'):
        if language_code == 'en' or not self.description_translations:
            return self.description
        return self.description_translations.get(language_code, self.description)

    def get_shop_full_address(self):
        """Generate full address string for shop"""
        parts = []

        if self.street_address:
            parts.append(self.street_address)
        if self.township:
            parts.append(self.township.name)
        if self.city:
            parts.append(self.city.name)
        if self.state:
            parts.append(self.state.name)

        return ", ".join(parts) if parts else self.address or "No address"

    def get_location_for_shipping(self):
        """Get location data for shipping calculation"""
        return {
            'state': self.state,
            'city': self.city,
            'township': self.township
        }

    class Meta:
        verbose_name_plural = "Shops"
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def shop_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' %(self.image.url))
    
    def __str__(self):
        return self.title

class Brand(models.Model):
    b_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="brand", alphabet="abcdefghi12345")
    title = models.CharField(max_length=100, default="Apple")
    
    title_translations = JSONField(default=dict, blank=True)
    
    brand_image = models.ImageField(upload_to="brand", default="brand.jpg")

    def get_translated_title(self, language_code='en'):
        if language_code == 'en' or not self.title_translations:
            return self.title
        return self.title_translations.get(language_code, self.title)
    class Meta:
        verbose_name_plural = "Brands"

    def brand_image_display(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % self.brand_image.url)

    def __str__(self):
        return self.title
    

logger = logging.getLogger(__name__)
    
class ExchangeRate(models.Model):
    """Centralized exchange rate management"""
    currency_from = models.CharField(max_length=3, default='USD')
    currency_to = models.CharField(max_length=3, default='MMK')
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    markup_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Additional markup percentage for exchange rate"
    )
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        unique_together = ['currency_from', 'currency_to']
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
    
    def get_effective_rate(self):
        """Get rate with markup applied"""
        if self.markup_percentage:
            return self.rate * (1 + self.markup_percentage / 100)
        return self.rate
    
    @classmethod
    def get_current_rate(cls, from_currency='USD', to_currency='MMK'):
        """Get current exchange rate without caching"""
        try:
            exchange_rate = cls.objects.get(
                currency_from=from_currency,
                currency_to=to_currency,
                is_active=True
            )
            return exchange_rate.get_effective_rate()
        except cls.DoesNotExist:
            return Decimal('3500')  # Default fallback rate
        
       
    
    def __str__(self):
        return f"{self.currency_from} to {self.currency_to}: {self.rate}"
    
class Product(models.Model):
    p_id = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghi12345")
    user = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete = models.SET_NULL, null=True,related_name="category")
    shop = models.ForeignKey(Shop, on_delete = models.SET_NULL, null=True, blank=True, related_name="shop_products")  # Optional: for reverse relation
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="brand_products")  # Optional: for reverse relation
    product_status = models.CharField(choices=STATUS, max_length=10, default="in_review")

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    stock_count = models.IntegerField(default=10)
    
    # Enhanced Inventory Fields
    min_stock_level = models.IntegerField(default=5, help_text="Minimum stock level before low stock alert")
    max_stock_level = models.IntegerField(default=100, help_text="Maximum stock capacity")
    reserved_stock = models.IntegerField(default=0, help_text="Stock reserved for pending orders")
    damaged_stock = models.IntegerField(default=0, help_text="Damaged/defective stock count")
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)
    
    sku = ShortUUIDField(unique=True, length=10, max_length=20,prefix = "sku", alphabet="1234567890")
    
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)
    ##### These are addtional for product detail #######
    
    title = models.CharField(max_length=100, default="Macbook")
    title_translations = JSONField(default=dict, blank=True)
    
    
    image = models.ImageField(upload_to=user_directory_path, default="product.jpg")
    
    description = models.TextField(null=True, blank=True, default="This is the product")
    description_translations = JSONField(default=dict, blank=True)
    
    cpu =models.CharField(max_length=100, default="intel")
    ram=models.CharField(max_length=100, default="8 GB")
    

    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    old_price = models.DecimalField(max_digits=12, decimal_places=2, default="2.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    
    # Add currency display preference (optional)
    display_currency_preference = models.CharField(
        max_length=10,
        choices=[('USD', 'USD Only'), ('MMK', 'MMK Only'), ('BOTH', 'Both')],
        default='BOTH'
    )
    
    specification = models.TextField(null=True, blank=True)
    specification_translations = JSONField(default=dict, blank=True)
    #tags = models.ForeignKey(Tags, on_delete=models.SET_NULL, null= True)
    
    # Translation metadata
    last_translated = models.DateTimeField(null=True, blank=True)
    translation_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    class Meta:
        verbose_name_plural = "Products"
        
    # Translation getter methods
    def get_translated_title(self, language_code='en'):
        if language_code == 'en' or not self.title_translations:
            return self.title
        return self.title_translations.get(language_code, self.title)
    
    def get_translated_description(self, language_code='en'):
        if language_code == 'en' or not self.description_translations:
            return self.description
        return self.description_translations.get(language_code, self.description)
    
    def get_translated_specification(self, language_code='en'):
        if language_code == 'en' or not self.specification_translations:
            return self.specification
        return self.specification_translations.get(language_code, self.specification)  
    
    def get_price_mmk(self):
        """Convert USD price to MMK"""
        rate = ExchangeRate.get_current_rate('USD', 'MMK')
        return self.price * rate
    
    def get_old_price_mmk(self):
        """Convert old USD price to MMK"""
        rate = ExchangeRate.get_current_rate('USD', 'MMK')
        return self.old_price * rate
    
    def get_display_price(self, language_code=None):
        """Get formatted price based on language"""
        from .utils import format_price_display
        
        if language_code is None:
            language_code = translation.get_language()
        
        return format_price_display(
            self.price, 
            self.old_price,
            language_code,
            self.display_currency_preference
        )
    
    def get_savings_amount(self):
        """Calculate savings in USD"""
        if self.old_price and self.old_price > self.price:
            return self.old_price - self.price
        return Decimal('0')
    
    def get_savings_amount_mmk(self):
        """Calculate savings in MMK"""
        rate = ExchangeRate.get_current_rate('USD', 'MMK')
        return self.get_savings_amount() * rate  
    
    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' %(self.image.url))
    
    def __str__(self):
        return self.title

    def get_percentage(self):         #this is for discount item
        # new_price / total_price
        #?. * 100
        new_price = ((self.old_price - self.price) / self.old_price ) * 100
        # new_price = (self.price / self.old_price) * 100
        return new_price
    
    # Enhanced Inventory Management Methods
    def get_available_stock(self):
        """Get actual available stock (total - reserved - damaged)"""
        return max(0, self.stock_count - self.reserved_stock - self.damaged_stock)
    
    def is_low_stock(self):
        """Check if product is running low on stock"""
        return self.get_available_stock() <= self.min_stock_level
    
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.get_available_stock() <= 0
    
    def can_fulfill_order(self, quantity):
        """Check if we can fulfill an order of given quantity"""
        return self.get_available_stock() >= quantity
    
    def reserve_stock(self, quantity):
        """Reserve stock for pending orders"""
        if self.can_fulfill_order(quantity):
            self.reserved_stock += quantity
            self.save()
            return True
        return False
    
    def release_reserved_stock(self, quantity):
        """Release reserved stock (e.g., when order is cancelled)"""
        self.reserved_stock = max(0, self.reserved_stock - quantity)
        self.save()
    
    def fulfill_order(self, quantity):
        """Fulfill an order by reducing stock and reserved stock"""
        if self.reserved_stock >= quantity:
            self.stock_count -= quantity
            self.reserved_stock -= quantity
            if self.stock_count <= 0:
                self.in_stock = False
            self.save()
            return True
        return False
    
    def restock(self, quantity, cost_per_unit=None):
        """Add stock to inventory"""
        self.stock_count += quantity
        if self.stock_count > 0:
            self.in_stock = True
        self.save()
        
        # Log the restock event
        InventoryLog.objects.create(
            product=self,
            action='restock',
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            notes=f"Restocked {quantity} units"
        )
    
    def mark_damaged(self, quantity, reason=""):
        """Mark stock as damaged"""
        if self.stock_count >= quantity:
            self.damaged_stock += quantity
            self.stock_count -= quantity
            if self.stock_count <= 0:
                self.in_stock = False
            self.save()
            
            # Log the damage
            InventoryLog.objects.create(
                product=self,
                action='damage',
                quantity=quantity,
                notes=f"Marked {quantity} units as damaged. Reason: {reason}"
            )
            return True
        return False
    
    # Review and Rating Methods
    def get_average_rating(self):
        """Calculate average rating from all approved reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
        return 0
    
    def get_rating_breakdown(self):
        """Get count of each rating (1-5 stars)"""
        breakdown = {}
        reviews = self.reviews.filter(is_approved=True)
        for i in range(1, 6):
            breakdown[i] = reviews.filter(rating=i).count()
        return breakdown
    
    def get_review_count(self):
        """Get total number of approved reviews"""
        return self.reviews.filter(is_approved=True).count()
    
    def get_verified_review_count(self):
        """Get count of verified purchase reviews"""
        return self.reviews.filter(is_approved=True, is_verified_purchase=True).count()
    
    def has_user_reviewed(self, user):
        """Check if user has already reviewed this product"""
        if not user.is_authenticated:
            return False
        return self.reviews.filter(user=user).exists()
    
    def can_user_review(self, user):
        """Check if user can review (must have purchased and not reviewed yet)"""
        if not user.is_authenticated or self.has_user_reviewed(user):
            return False
        
        # Check if user has purchased this product
        has_purchased = CartOrderItem.objects.filter(
            order__user=user,
            product=self,
            order__product_status='delivered'
        ).exists()
        
        return has_purchased
    
    # Recommendation Methods
    def get_similar_products(self, limit=5):
        """Get similar products based on pre-calculated similarities"""
        similar_ids = ProductSimilarity.objects.filter(
            product_1=self
        ).order_by('-similarity_score').values_list('product_2_id', flat=True)[:limit]
        
        return Product.objects.filter(id__in=similar_ids, status=True, in_stock=True)
    
    def get_frequently_bought_together(self, limit=5):
        """Get products frequently bought with this one"""
        # Find orders that contain this product
        orders_with_product = CartOrderItem.objects.filter(product=self).values_list('order_id', flat=True)
        
        # Find other products in those orders
        other_products = CartOrderItem.objects.filter(
            order_id__in=orders_with_product
        ).exclude(product=self).values('product').annotate(
            count=models.Count('product')
        ).order_by('-count')[:limit]
        
        product_ids = [item['product'] for item in other_products]
        return Product.objects.filter(id__in=product_ids, status=True, in_stock=True)

class InventoryLog(models.Model):
    """Track all inventory movements and changes"""
    ACTION_CHOICES = (
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('damage', 'Damaged'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('reserve', 'Reserve'),
        ('release', 'Release Reserved'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField()
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Stock levels after this action
    stock_after = models.IntegerField(null=True, blank=True)
    reserved_after = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Inventory Log"
        verbose_name_plural = "Inventory Logs"
    
    def __str__(self):
        return f"{self.product.title} - {self.get_action_display()} ({self.quantity})"

class SupplierContact(models.Model):
    """Supplier information for restocking"""
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    products = models.ManyToManyField(Product, through='SupplierProduct')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Supplier Contact"
        verbose_name_plural = "Supplier Contacts"
    
    def __str__(self):
        return f"{self.name} ({self.company})"

class SupplierProduct(models.Model):
    """Relationship between suppliers and products with pricing"""
    supplier = models.ForeignKey(SupplierContact, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.IntegerField(default=1)
    lead_time_days = models.IntegerField(default=7)
    is_preferred = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['supplier', 'product']
        verbose_name = "Supplier Product"
        verbose_name_plural = "Supplier Products"
    
    def __str__(self):
        return f"{self.supplier.name} - {self.product.title}"
    
class ProductImages(models.Model):
    images  = models.ImageField(upload_to="product-image", default="product.jpg")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null = True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Images"

#################################### Cart, Order, OrderItem ##########################     
#################################### Cart, Order, OrderItem ##########################     
#################################### Cart, Order, OrderItem ##########################
     
class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99")
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=20, default="pending")
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=[('home', 'Home'), ('shop', 'Shop')], default='home')
    
    # Enhanced Order Tracking Fields
    order_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    
    # Delivery Information
    delivery_address = models.TextField(blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Status Timestamps
    confirmed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    packed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Fields
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment Information
    PAYMENT_METHODS = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('kbzpay', 'KBZPay'),
        ('cod', 'Cash on Delivery'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal')

    # Payment Intent IDs for tracking
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    paypal_payment_intent = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Cart Orders"
        ordering = ['-order_date']
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"CO{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_order_progress(self):
        """Get order progress percentage"""
        status_progress = {
            'pending': 10,
            'confirmed': 20,
            'processing': 40,
            'packed': 60,
            'shipped': 80,
            'out_for_delivery': 90,
            'delivered': 100,
            'cancelled': 0,
            'returned': 0,
            'refunded': 0,
        }
        return status_progress.get(self.product_status, 0)
    
    def get_status_display_with_time(self):
        """Get status with timestamp"""
        status_times = {
            'confirmed': self.confirmed_at,
            'processing': self.processed_at,
            'packed': self.packed_at,
            'shipped': self.shipped_at,
            'delivered': self.delivered_at,
        }
        time = status_times.get(self.product_status)
        if time:
            return f"{self.get_product_status_display()} - {time.strftime('%Y-%m-%d %H:%M')}"
        return self.get_product_status_display()
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.product_status in ['pending', 'confirmed', 'processing']
    
    def can_be_returned(self):
        """Check if order can be returned"""
        return self.product_status == 'delivered' and self.delivered_at
    
    def get_total_items(self):
        """Get total number of items in order"""
        return self.cartorderitem_set.aggregate(total=models.Sum('qty'))['total'] or 0

class OrderStatusHistory(models.Model):
    """Track all status changes for orders"""
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(choices=STATUS_CHOICE, max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Location tracking
    location = models.CharField(max_length=200, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"Order {self.order.order_number} - {self.get_status_display()}"

class CartOrderItem(models.Model):
    
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True) 
    
    invoice_no= models.CharField(max_length=200)
    product_status = models.CharField(max_length=200)
    item = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    total = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    
    class Meta:
        verbose_name_plural = "Cart Order Item"
        
    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' %(self.image.url))
        
    def order_img(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" />' %(self.image))
    
    

#################################### Product Review, Wishlists, Address ##########################     
#################################### Product Review, Wishlists, Address ##########################     
#################################### Product Review, Wishlists, Address ##########################
     
     
class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='reviews')
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Enhanced Review Fields
    title = models.CharField(max_length=200, blank=True)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=5)
    
    # Detailed Ratings
    quality_rating = models.IntegerField(choices=RATING, default=5)
    value_rating = models.IntegerField(choices=RATING, default=5)
    delivery_rating = models.IntegerField(choices=RATING, default=5)
    
    # Review Status
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    # Meta
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Product Reviews"
        unique_together = ['user', 'product']  # One review per user per product
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}⭐)"
    
    def get_rating(self):
        return self.rating
    
    def get_average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        return (self.quality_rating + self.value_rating + self.delivery_rating) / 3
    
    def save(self, *args, **kwargs):
        # Check if this is a verified purchase
        if self.order and self.order.user == self.user and self.order.product_status == 'delivered':
            self.is_verified_purchase = True
        super().save(*args, **kwargs)

class ReviewHelpful(models.Model):
    """Track helpful votes for reviews"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='votes')
    is_helpful = models.BooleanField()  # True for helpful, False for unhelpful
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'review']
        verbose_name = "Review Vote"
        verbose_name_plural = "Review Votes"
    
    def __str__(self):
        vote_type = "Helpful" if self.is_helpful else "Unhelpful"
        return f"{self.user.username} - {vote_type}"

class ReviewImage(models.Model):
    """Allow users to upload images with reviews"""
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review-images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Review Image"
        verbose_name_plural = "Review Images"
    
    def __str__(self):
        return f"Image for {self.review}"

class ReviewReport(models.Model):
    """Allow users to report inappropriate reviews"""
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('other', 'Other'),
    )
    
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'reported_by']
        verbose_name = "Review Report"
        verbose_name_plural = "Review Reports"
    
    def __str__(self):
        return f"Report: {self.get_reason_display()}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete = models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Wishlists"
        
    def __str__(self):
        return self.product.title

class Address(models.Model):
    user = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
    mobile = models.CharField(max_length=100, null = True)

    # Detailed location fields
    state = models.ForeignKey(MyanmarState, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(MyanmarCity, on_delete=models.SET_NULL, null=True)
    township = models.ForeignKey(MyanmarTownship, on_delete=models.SET_NULL, null=True, blank=True)

    # Detailed address components
    street_address = models.CharField(max_length=200, null=True, blank=True, help_text="Street No, Building, etc.")
    landmark = models.CharField(max_length=100, null=True, blank=True, help_text="Near landmark")

    # Legacy address field for backward compatibility
    address = models.CharField(max_length=100, null = True, blank=True)

    status = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = "Address"

    def get_full_address(self):
        """Generate full address string"""
        parts = []

        if self.street_address:
            parts.append(self.street_address)
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        if self.township:
            parts.append(self.township.name)
        if self.city:
            parts.append(self.city.name)
        if self.state:
            parts.append(self.state.name)

        return ", ".join(parts) if parts else self.address or "No address"

    def get_location_for_shipping(self):
        """Get location data for shipping calculation"""
        return {
            'state': self.state,
            'city': self.city,
            'township': self.township
        }

    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.get_full_address()}"

#################################### Recommendation Engine ##########################     
#################################### Recommendation Engine ##########################     
#################################### Recommendation Engine ##########################

class UserBehavior(models.Model):
    """Track user behavior for recommendation engine"""
    ACTION_CHOICES = (
        ('view', 'Product View'),
        ('cart_add', 'Add to Cart'),
        ('cart_remove', 'Remove from Cart'),
        ('wishlist_add', 'Add to Wishlist'),
        ('wishlist_remove', 'Remove from Wishlist'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('search', 'Search'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behaviors')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Additional context
    search_query = models.CharField(max_length=200, blank=True)  # For search actions
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Scoring
    score = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)  # Weight for recommendation
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Behavior"
        verbose_name_plural = "User Behaviors"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['product', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        if self.product:
            return f"{self.user.username} - {self.get_action_display()} - {self.product.title}"
        return f"{self.user.username} - {self.get_action_display()}"

class ProductSimilarity(models.Model):
    """Store pre-calculated product similarities for faster recommendations"""
    product_1 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_products')
    product_2 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_to')
    similarity_score = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0 to 1.0
    
    # Similarity factors
    category_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.3)
    brand_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.2)
    price_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.2)
    feature_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.3)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product_1', 'product_2']
        verbose_name = "Product Similarity"
        verbose_name_plural = "Product Similarities"
        indexes = [
            models.Index(fields=['product_1', 'similarity_score']),
            models.Index(fields=['similarity_score']),
        ]
    
    def __str__(self):
        return f"{self.product_1.title} ↔ {self.product_2.title} ({self.similarity_score})"

class RecommendationList(models.Model):
    """Store personalized recommendation lists for users"""
    RECOMMENDATION_TYPES = (
        ('popular', 'Popular Products'),
        ('trending', 'Trending Products'),
        ('similar', 'Similar Products'),
        ('collaborative', 'Users Also Bought'),
        ('content', 'Content-Based'),
        ('seasonal', 'Seasonal Picks'),
        ('price_drop', 'Price Drops'),
        ('new_arrival', 'New Arrivals'),
        ('category_best', 'Best in Category'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_lists')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    products = models.ManyToManyField(Product, through='RecommendationItem')
    
    # Context
    based_on_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, 
                                       related_name='generated_recommendations')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Recommendations expire after some time
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Recommendation List"
        verbose_name_plural = "Recommendation Lists"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_recommendation_type_display()}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

class RecommendationItem(models.Model):
    """Individual items in recommendation lists with scores"""
    recommendation_list = models.ForeignKey(RecommendationList, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=8, decimal_places=4)
    rank = models.PositiveIntegerField()  # Position in the list
    
    # Explanation for the recommendation
    reason = models.CharField(max_length=200, blank=True)  # Why this was recommended
    
    class Meta:
        unique_together = ['recommendation_list', 'product']
        ordering = ['rank']
        verbose_name = "Recommendation Item"
        verbose_name_plural = "Recommendation Items"
    
    def __str__(self):
        return f"#{self.rank} {self.product.title} (Score: {self.score})"

#################################### Analytics and Reporting ##########################     
#################################### Analytics and Reporting ##########################     
#################################### Analytics and Reporting ##########################

class ProductAnalytics(models.Model):
    """Daily analytics for products"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # View metrics
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    cart_adds = models.PositiveIntegerField(default=0)
    cart_removes = models.PositiveIntegerField(default=0)
    wishlist_adds = models.PositiveIntegerField(default=0)
    
    # Purchase metrics
    purchases = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Conversion metrics
    view_to_cart_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    cart_to_purchase_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    
    class Meta:
        unique_together = ['product', 'date']
        verbose_name = "Product Analytics"
        verbose_name_plural = "Product Analytics"
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['product', 'date']),
        ]
    
    def __str__(self):
        return f"{self.product.title} - {self.date}"

class SalesAnalytics(models.Model):
    """Daily sales analytics"""
    date = models.DateField(unique=True)
    
    # Sales metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_items_sold = models.PositiveIntegerField(default=0)
    
    # Customer metrics
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    
    # Order metrics
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    returned_orders = models.PositiveIntegerField(default=0)
    
    # Popular items
    most_viewed_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, 
                                          related_name='most_viewed_days')
    best_selling_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='best_selling_days')
    
    class Meta:
        verbose_name = "Sales Analytics"
        verbose_name_plural = "Sales Analytics"
        ordering = ['-date']
    
    def __str__(self):
        return f"Sales Analytics - {self.date}"

class CustomerAnalytics(models.Model):
    """Track customer behavior and lifetime value"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Purchase behavior
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Engagement metrics
    total_product_views = models.PositiveIntegerField(default=0)
    total_cart_adds = models.PositiveIntegerField(default=0)
    total_wishlist_adds = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Customer segments
    CUSTOMER_SEGMENTS = (
        ('new', 'New Customer'),
        ('regular', 'Regular Customer'),
        ('vip', 'VIP Customer'),
        ('inactive', 'Inactive Customer'),
    )
    segment = models.CharField(max_length=10, choices=CUSTOMER_SEGMENTS, default='new')
    
    # Dates
    first_purchase_date = models.DateTimeField(null=True, blank=True)
    last_purchase_date = models.DateTimeField(null=True, blank=True)
    last_activity_date = models.DateTimeField(null=True, blank=True)
    
    # Preferences (inferred from behavior)
    preferred_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    average_price_range = models.CharField(max_length=50, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer Analytics"
        verbose_name_plural = "Customer Analytics"
    
    def __str__(self):
        return f"{self.user.username} Analytics"
    
    def calculate_lifetime_value(self):
        """Calculate customer lifetime value"""
        if self.total_orders > 0:
            return float(self.total_spent)
        return 0
    
    def update_segment(self):
        """Update customer segment based on behavior"""
        if self.total_orders == 0:
            self.segment = 'new'
        elif self.total_orders >= 10 or self.total_spent >= 1000:
            self.segment = 'vip'
        elif self.total_orders >= 3:
            self.segment = 'regular'
        elif self.last_activity_date and (timezone.now() - self.last_activity_date).days > 90:
            self.segment = 'inactive'
        else:
            self.segment = 'regular'
        
        self.save()

#################################### Email Notifications ##########################     
#################################### Email Notifications ##########################     
#################################### Email Notifications ##########################

class EmailTemplate(models.Model):
    """Email templates for various notifications"""
    EMAIL_TYPES = (
        ('welcome', 'Welcome Email'),
        ('order_confirmation', 'Order Confirmation'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('password_reset', 'Password Reset'),
        ('low_stock', 'Low Stock Alert'),
        ('abandoned_cart', 'Abandoned Cart'),
        ('review_request', 'Review Request'),
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
    )
    
    name = models.CharField(max_length=100)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_email_type_display()})"

class EmailLog(models.Model):
    """Log all sent emails"""
    EMAIL_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    email_type = models.CharField(max_length=20, choices=EmailTemplate.EMAIL_TYPES)
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=EMAIL_STATUS, default='pending')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Context data (JSON field for dynamic content)
    context_data = models.JSONField(default=dict, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient_email} - {self.get_email_type_display()}"

#################################### Social Media Integration ##########################     
#################################### Social Media Integration ##########################     
#################################### Social Media Integration ##########################

class SocialMediaAccount(models.Model):
    """Store social media accounts for sharing"""
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('youtube', 'YouTube'),
    )
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_name = models.CharField(max_length=100)
    account_url = models.URLField()
    account_id = models.CharField(max_length=100, blank=True)  # Platform-specific ID
    access_token = models.TextField(blank=True)  # For API access
    
    is_active = models.BooleanField(default=True)
    is_auto_post = models.BooleanField(default=False)  # Auto-post new products
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Social Media Account"
        verbose_name_plural = "Social Media Accounts"
    
    def __str__(self):
        return f"{self.get_platform_display()} - {self.account_name}"

class SocialMediaPost(models.Model):
    """Track social media posts"""
    POST_STATUS = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    )
    
    account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='posts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='social_posts')
    
    content = models.TextField()
    image_url = models.URLField(blank=True)
    post_url = models.URLField(blank=True)  # URL of published post
    
    status = models.CharField(max_length=10, choices=POST_STATUS, default='draft')
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Social Media Post"
        verbose_name_plural = "Social Media Posts"
        ordering = ['-created_at']
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.account.get_platform_display()} - {content_preview}"


class CheckoutSession(models.Model):
    """Temporary storage for checkout data during payment processing"""
    session_id = ShortUUIDField(unique=True, length=20, max_length=40, alphabet="abcdefgh12345")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE)

    # Address data
    state = models.ForeignKey(MyanmarState, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(MyanmarCity, on_delete=models.CASCADE, null=True, blank=True)
    township = models.ForeignKey(MyanmarTownship, on_delete=models.CASCADE, null=True, blank=True)
    street_address = models.TextField(blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Cart data
    cart_data = JSONField(default=dict)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Payment method
    payment_method = models.CharField(max_length=20, choices=[
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('kbzpay', 'KBZPay'),
        ('cod', 'Cash on Delivery'),
    ])

    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Checkout Session"
        verbose_name_plural = "Checkout Sessions"
        ordering = ['-created_at']

    def __str__(self):
        return f"Checkout {self.session_id} - {self.user.username} - {self.shop.title}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 30 minutes from creation
            self.expires_at = timezone.now() + timezone.timedelta(minutes=30)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def get_delivery_address(self):
        """Build formatted delivery address string"""
        if not self.state or not self.city:
            return ""

        parts = []
        if self.street_address:
            parts.append(self.street_address)
        if self.township:
            parts.append(self.township.name)
        parts.extend([self.city.name, self.state.name])
        if self.landmark:
            parts.append(f"Near {self.landmark}")

        return ", ".join(parts)
 