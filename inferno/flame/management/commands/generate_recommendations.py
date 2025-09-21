from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q, F
from flame.models import (
    Product, UserBehavior, ProductSimilarity, RecommendationList, 
    RecommendationItem, User, CartOrderItem, Category
)
from datetime import timedelta
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate product recommendations for users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate recommendations for specific user ID'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of users to process in batch. Default is 50.'
        )
        parser.add_argument(
            '--recalculate-similarities',
            action='store_true',
            help='Recalculate product similarities before generating recommendations'
        )
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        batch_size = options.get('batch_size', 50)
        recalculate = options.get('recalculate_similarities', False)
        
        if recalculate:
            self.calculate_product_similarities()
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.generate_user_recommendations(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Generated recommendations for user {user.username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} does not exist')
                )
        else:
            # Process users in batches
            users = User.objects.filter(is_active=True)
            total_users = users.count()
            
            for i in range(0, total_users, batch_size):
                batch = users[i:i+batch_size]
                for user in batch:
                    self.generate_user_recommendations(user)
                
                self.stdout.write(
                    f'Processed {min(i+batch_size, total_users)}/{total_users} users'
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Generated recommendations for {total_users} users')
            )
    
    def calculate_product_similarities(self):
        """Calculate product similarities based on various factors"""
        self.stdout.write('Calculating product similarities...')
        
        products = Product.objects.filter(status=True, in_stock=True)
        total_products = products.count()
        processed = 0
        
        for product1 in products:
            similar_products = products.exclude(id=product1.id)
            
            for product2 in similar_products:
                # Skip if similarity already calculated
                if ProductSimilarity.objects.filter(
                    Q(product_1=product1, product_2=product2) |
                    Q(product_1=product2, product_2=product1)
                ).exists():
                    continue
                
                similarity_score = self.calculate_similarity_score(product1, product2)
                
                if similarity_score > 0.1:  # Only store significant similarities
                    ProductSimilarity.objects.create(
                        product_1=product1,
                        product_2=product2,
                        similarity_score=similarity_score
                    )
            
            processed += 1
            if processed % 10 == 0:
                self.stdout.write(f'Processed {processed}/{total_products} products')
    
    def calculate_similarity_score(self, product1, product2):
        """Calculate similarity score between two products"""
        score = Decimal('0.0')
        
        # Category similarity (30% weight)
        if product1.category and product2.category:
            if product1.category == product2.category:
                score += Decimal('0.3')
        
        # Brand similarity (20% weight)
        if product1.brand and product2.brand:
            if product1.brand == product2.brand:
                score += Decimal('0.2')
        
        # Price similarity (20% weight)
        if product1.price and product2.price:
            price_diff = abs(product1.price - product2.price)
            max_price = max(product1.price, product2.price)
            if max_price > 0:
                price_similarity = 1 - (price_diff / max_price)
                score += Decimal('0.2') * Decimal(str(price_similarity))
        
        # Feature similarity (30% weight) - based on specs
        feature_score = Decimal('0.0')
        if product1.cpu and product2.cpu:
            if product1.cpu.lower() in product2.cpu.lower() or product2.cpu.lower() in product1.cpu.lower():
                feature_score += Decimal('0.15')
        
        if product1.ram and product2.ram:
            if product1.ram.lower() in product2.ram.lower() or product2.ram.lower() in product1.ram.lower():
                feature_score += Decimal('0.15')
        
        score += feature_score
        
        return min(score, Decimal('1.0'))  # Cap at 1.0
    
    def generate_user_recommendations(self, user):
        """Generate recommendations for a specific user"""
        # Clear existing recommendations older than 7 days
        old_cutoff = timezone.now() - timedelta(days=7)
        RecommendationList.objects.filter(
            user=user,
            created_at__lt=old_cutoff
        ).delete()
        
        # Generate different types of recommendations
        self.generate_popular_recommendations(user)
        self.generate_collaborative_recommendations(user)
        self.generate_content_based_recommendations(user)
        self.generate_trending_recommendations(user)
    
    def generate_popular_recommendations(self, user):
        """Generate popular product recommendations"""
        # Get most ordered products in last 30 days
        popular_products = Product.objects.filter(
            status=True,
            in_stock=True
        ).annotate(
            order_count=Count('cartorderitem__order', 
                            filter=Q(cartorderitem__order__order_date__gte=timezone.now()-timedelta(days=30)))
        ).order_by('-order_count')[:20]
        
        # Exclude products user already bought
        user_bought_products = CartOrderItem.objects.filter(
            order__user=user
        ).values_list('product_id', flat=True)
        
        popular_products = popular_products.exclude(id__in=user_bought_products)[:10]
        
        if popular_products:
            rec_list = RecommendationList.objects.create(
                user=user,
                recommendation_type='popular',
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            for rank, product in enumerate(popular_products, 1):
                RecommendationItem.objects.create(
                    recommendation_list=rec_list,
                    product=product,
                    rank=rank,
                    score=Decimal('1.0') - Decimal('0.05') * (rank - 1),
                    reason="Popular among customers"
                )
    
    def generate_collaborative_recommendations(self, user):
        """Generate collaborative filtering recommendations"""
        # Find users with similar purchase history
        user_products = set(CartOrderItem.objects.filter(
            order__user=user
        ).values_list('product_id', flat=True))
        
        if not user_products:
            return
        
        # Find users who bought similar products
        similar_users = User.objects.filter(
            cartorder__cartorderitem__product_id__in=user_products
        ).exclude(id=user.id).annotate(
            common_products=Count('cartorder__cartorderitem__product', 
                                filter=Q(cartorder__cartorderitem__product_id__in=user_products))
        ).filter(common_products__gte=2).order_by('-common_products')[:10]
        
        # Get products bought by similar users
        recommended_products = Product.objects.filter(
            cartorderitem__order__user__in=similar_users,
            status=True,
            in_stock=True
        ).exclude(
            id__in=user_products
        ).annotate(
            similarity_score=Count('cartorderitem__order__user', distinct=True)
        ).order_by('-similarity_score')[:10]
        
        if recommended_products:
            rec_list = RecommendationList.objects.create(
                user=user,
                recommendation_type='collaborative',
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            for rank, product in enumerate(recommended_products, 1):
                RecommendationItem.objects.create(
                    recommendation_list=rec_list,
                    product=product,
                    rank=rank,
                    score=Decimal('0.9') - Decimal('0.05') * (rank - 1),
                    reason="Customers with similar taste also bought"
                )
    
    def generate_content_based_recommendations(self, user):
        """Generate content-based recommendations using product similarities"""
        # Get user's recent product interactions
        recent_behaviors = UserBehavior.objects.filter(
            user=user,
            product__isnull=False,
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).order_by('-timestamp')[:5]
        
        if not recent_behaviors:
            return
        
        recommended_products = []
        for behavior in recent_behaviors:
            # Find similar products
            similarities = ProductSimilarity.objects.filter(
                product_1=behavior.product
            ).order_by('-similarity_score')[:3]
            
            for similarity in similarities:
                if similarity.product_2 not in recommended_products:
                    recommended_products.append((
                        similarity.product_2, 
                        similarity.similarity_score,
                        f"Similar to {behavior.product.title}"
                    ))
        
        # Sort by similarity score and take top 10
        recommended_products.sort(key=lambda x: x[1], reverse=True)
        recommended_products = recommended_products[:10]
        
        if recommended_products:
            rec_list = RecommendationList.objects.create(
                user=user,
                recommendation_type='content',
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            for rank, (product, score, reason) in enumerate(recommended_products, 1):
                RecommendationItem.objects.create(
                    recommendation_list=rec_list,
                    product=product,
                    rank=rank,
                    score=score,
                    reason=reason
                )
    
    def generate_trending_recommendations(self, user):
        """Generate trending product recommendations"""
        # Get products with highest view-to-purchase ratio in last 7 days
        trending_products = Product.objects.filter(
            status=True,
            in_stock=True
        ).annotate(
            recent_views=Count('userbehavior', 
                             filter=Q(userbehavior__action='view', 
                                     userbehavior__timestamp__gte=timezone.now()-timedelta(days=7))),
            recent_purchases=Count('cartorderitem__order',
                                 filter=Q(cartorderitem__order__order_date__gte=timezone.now()-timedelta(days=7)))
        ).filter(
            recent_views__gt=10
        ).order_by('-recent_views')[:10]
        
        if trending_products:
            rec_list = RecommendationList.objects.create(
                user=user,
                recommendation_type='trending',
                expires_at=timezone.now() + timedelta(days=3)  # Shorter expiry for trending
            )
            
            for rank, product in enumerate(trending_products, 1):
                RecommendationItem.objects.create(
                    recommendation_list=rec_list,
                    product=product,
                    rank=rank,
                    score=Decimal('0.8') - Decimal('0.03') * (rank - 1),
                    reason="Trending now"
                )