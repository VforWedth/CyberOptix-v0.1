from django.db import models
from django.db.models import JSONField
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from django.utils.text import slugify
from django.core.cache import cache
from decimal import Decimal
from django.utils import translation
from django.conf import settings
import logging

STATUS_CHOICE = (
    ("processing","Processing"),
    ("shipped","Shipped"),
    ("deliverd","Delivered"),
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
    
    def get_translated_title(self, language_code='en'):
        if language_code == 'en' or not self.title_translations:
            return self.title
        return self.title_translations.get(language_code, self.title)
    
    def get_translated_description(self, language_code='en'):
        if language_code == 'en' or not self.description_translations:
            return self.description
        return self.description_translations.get(language_code, self.description)
    
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
    stock_count = models.CharField(max_length=100, default="10")
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
    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=10, default="processing")
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=[('home', 'Home'), ('shop', 'Shop')], default='home')
    class Meta:
        verbose_name_plural = "Cart Order"

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
    user = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete = models.SET_NULL, null=True)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Reviews"
        
    def __str__(self):
        return self.product.title
    
    def get_rating(self):
        return self.rating
    
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
    address = models.CharField(max_length=100, null = True)
    status = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Address"
    
 