from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from django.utils.text import slugify
from django.utils import timezone
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
    image = models.ImageField(upload_to="category", default="category.jpg")
    
    class Meta:
        verbose_name_plural = "Categories"
        
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
    brand_image = models.ImageField(upload_to="brand", default="brand.jpg")

    class Meta:
        verbose_name_plural = "Brands"

    def brand_image_display(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % self.brand_image.url)

    def __str__(self):
        return self.title
    
    
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
    image = models.ImageField(upload_to=user_directory_path, default="product.jpg")
    description = models.TextField(null=True, blank=True, default="This is the product")
    cpu =models.CharField(max_length=100, default="intel")
    ram=models.CharField(max_length=100, default="8 GB")
    

    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    old_price = models.DecimalField(max_digits=12, decimal_places=2, default="2.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    
    specification = models.TextField(null=True, blank=True)
    #tags = models.ForeignKey(Tags, on_delete=models.SET_NULL, null= True)
    
    class Meta:
        verbose_name_plural = "Products"
        
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
from django.db.models import Sum  ,Count   
class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2, default="1.99") #dollar nk lote mhr lrr kyat pyaung mhr lrr
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=10, default="processing")
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=[('home', 'Home'), ('shop', 'Shop')], default='home')
    
    @property
    def formatted_price(self):
        """Format price with currency symbol"""
        return f"${self.price}"  # Adjust for your currency
    
    @classmethod
    def total_sales(cls):
        """Calculate total completed sales"""
        return cls.objects.filter(paid_status=True).aggregate(
            total_sales=models.Sum('price')
        )['total_sales'] or 0
    
    @classmethod
    def recent_sales(cls, days=30):
        """Sales for the last N days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            paid_status=True,
            order_date__gte=cutoff_date
        ).aggregate(total_sales=models.Sum('price'))['total_sales'] or 0
    
    @classmethod
    def sales_by_status(cls):
        """Sales grouped by product status"""
        return cls.objects.filter(paid_status=True).values('product_status').annotate(
            total_sales=models.Sum('price'),
            order_count=models.Count('id')
        ).order_by('-total_sales')
    
    @classmethod
    def shop_vs_home_sales(cls):
        """Compare shop vs home delivery sales"""
        return cls.objects.filter(paid_status=True).values('order_type').annotate(
            total_sales=models.Sum('price'),
            order_count=models.Count('id')
        ).order_by('-total_sales')
        
    @classmethod
    def total_orders(cls):
        """Count all orders (both paid and unpaid)"""
        return cls.objects.count()
    @classmethod
    def paid_orders_count(cls):
        """Count only paid orders"""
        return cls.objects.filter(paid_status=True).count()
    @classmethod
    def orders_by_status(cls):
        """Count orders grouped by their status"""
        return cls.objects.values('product_status').annotate(
            count=models.Count('id')
        ).order_by('-count')
    @classmethod
    def recent_orders_count(cls, days=30):
        """Count orders from last N days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(
            order_date__gte=cutoff_date
        ).count()
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
    @classmethod
    def top_selling_products(cls, limit=5):
        results = (
            cls.objects.filter(order__paid_status=True)
            .values("item", "price")  # use snapshot fields instead of FK
        .annotate(
            total_quantity=Sum("qty"),
            total_revenue=Sum("total")
        )
        .order_by("-total_quantity")[:limit]
    )
        return results


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
    
 