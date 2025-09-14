from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F
from flame.models import CartOrder, CartOrderItem, ProductAnalytics, SalesAnalytics, CustomerAnalytics, Product, User
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update order and sales analytics data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to process (YYYY-MM-DD format). Default is yesterday.'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to process backwards from date. Default is 1.'
        )
    
    def handle(self, *args, **options):
        target_date = options.get('date')
        days = options.get('days', 1)
        
        if target_date:
            try:
                target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD.')
                )
                return
        else:
            target_date = date.today() - timedelta(days=1)
        
        # Process multiple days if requested
        for i in range(days):
            process_date = target_date - timedelta(days=i)
            self.update_sales_analytics(process_date)
            self.update_product_analytics(process_date)
            self.update_customer_analytics()
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated analytics for {days} day(s)')
        )
    
    def update_sales_analytics(self, target_date):
        """Update daily sales analytics"""
        orders = CartOrder.objects.filter(order_date__date=target_date)
        
        analytics, created = SalesAnalytics.objects.get_or_create(
            date=target_date,
            defaults={
                'total_orders': 0,
                'total_revenue': 0,
                'total_items_sold': 0,
                'new_customers': 0,
                'returning_customers': 0,
                'average_order_value': 0,
                'cancelled_orders': 0,
                'returned_orders': 0,
            }
        )
        
        # Calculate metrics
        analytics.total_orders = orders.count()
        analytics.total_revenue = orders.aggregate(
            total=Sum('total_amount'))['total'] or 0
        analytics.total_items_sold = CartOrderItem.objects.filter(
            order__order_date__date=target_date
        ).aggregate(total=Sum('qty'))['total'] or 0
        
        if analytics.total_orders > 0:
            analytics.average_order_value = analytics.total_revenue / analytics.total_orders
        
        analytics.cancelled_orders = orders.filter(product_status='cancelled').count()
        analytics.returned_orders = orders.filter(product_status='returned').count()
        
        # Find new vs returning customers
        user_ids = orders.values_list('user_id', flat=True).distinct()
        new_customer_count = 0
        
        for user_id in user_ids:
            first_order = CartOrder.objects.filter(user_id=user_id).order_by('order_date').first()
            if first_order and first_order.order_date.date() == target_date:
                new_customer_count += 1
        
        analytics.new_customers = new_customer_count
        analytics.returning_customers = len(user_ids) - new_customer_count
        
        # Find most viewed and best selling products
        best_selling = CartOrderItem.objects.filter(
            order__order_date__date=target_date
        ).values('product').annotate(
            total_sold=Sum('qty')
        ).order_by('-total_sold').first()
        
        if best_selling:
            analytics.best_selling_product_id = best_selling['product']
        
        analytics.save()
        
        logger.info(f"Updated sales analytics for {target_date}")
    
    def update_product_analytics(self, target_date):
        """Update product analytics - this would typically be called by page view tracking"""
        # This is a placeholder - in a real system, you'd track these metrics
        # through user behavior tracking, which we've set up in the models
        pass
    
    def update_customer_analytics(self):
        """Update customer analytics for all users"""
        users = User.objects.filter(is_active=True)
        
        for user in users:
            analytics, created = CustomerAnalytics.objects.get_or_create(
                user=user
            )
            
            # Update purchase behavior
            orders = CartOrder.objects.filter(user=user, paid_status=True)
            analytics.total_orders = orders.count()
            analytics.total_spent = orders.aggregate(
                total=Sum('total_amount'))['total'] or 0
            
            if analytics.total_orders > 0:
                analytics.average_order_value = analytics.total_spent / analytics.total_orders
                analytics.first_purchase_date = orders.order_by('order_date').first().order_date
                analytics.last_purchase_date = orders.order_by('-order_date').first().order_date
            
            # Update engagement metrics from user behavior
            from flame.models import UserBehavior
            behaviors = UserBehavior.objects.filter(user=user)
            analytics.total_product_views = behaviors.filter(action='view').count()
            analytics.total_cart_adds = behaviors.filter(action='cart_add').count()
            analytics.total_wishlist_adds = behaviors.filter(action='wishlist_add').count()
            analytics.total_reviews = behaviors.filter(action='review').count()
            
            # Update preferred category and brand
            if orders.exists():
                # Find most ordered category
                category_counts = CartOrderItem.objects.filter(
                    order__user=user,
                    product__category__isnull=False
                ).values('product__category').annotate(
                    count=Count('product__category')
                ).order_by('-count').first()
                
                if category_counts:
                    from flame.models import Category
                    analytics.preferred_category = Category.objects.get(
                        id=category_counts['product__category']
                    )
                
                # Find most ordered brand
                brand_counts = CartOrderItem.objects.filter(
                    order__user=user,
                    product__brand__isnull=False
                ).values('product__brand').annotate(
                    count=Count('product__brand')
                ).order_by('-count').first()
                
                if brand_counts:
                    from flame.models import Brand
                    analytics.preferred_brand = Brand.objects.get(
                        id=brand_counts['product__brand']
                    )
            
            # Update customer segment
            analytics.update_segment()
            analytics.last_activity_date = timezone.now()
            analytics.save()
        
        logger.info("Updated customer analytics for all users")