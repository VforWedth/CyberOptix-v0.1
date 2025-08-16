# management/commands/translate_products.py
from django.core.management.base import BaseCommand
from django.db.models import Q
from flame.models import Product, Category, Shop, Brand
from flame.translation_service import translation_service
import time


class Command(BaseCommand):
    help = 'Translate products and related models to multiple languages'
    
    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, help='Model to translate (product, category, shop, brand)')
        parser.add_argument('--batch-size', type=int, default=10, help='Batch size for translation')
        parser.add_argument('--force', action='store_true', help='Force re-translation')
    
    def handle(self, *args, **options):
        model_name = options.get('model', 'product').lower()
        batch_size = options.get('batch_size', 10)
        force = options.get('force', False)
        
        model_configs = {
            'product': {
                'model': Product,
                'fields': ['title', 'description', 'cpu', 'ram', 'specification']
            },
            'category': {
                'model': Category,
                'fields': ['title']
            },
            'shop': {
                'model': Shop,
                'fields': ['title', 'description']
            },
            'brand': {
                'model': Brand,
                'fields': ['title']
            }
        }
        
        if model_name not in model_configs:
            self.stdout.write(
                self.style.ERROR(f'Unknown model: {model_name}')
            )
            return
        
        config = model_configs[model_name]
        Model = config['model']
        fields = config['fields']
        
        # Get objects to translate
        if force:
            queryset = Model.objects.all()
        else:
            queryset = Model.objects.filter(
                Q(last_translated__isnull=True) | 
                Q(translation_status='failed')
            ) if hasattr(Model, 'last_translated') else Model.objects.all()
        
        total = queryset.count()
        self.stdout.write(f'Found {total} {model_name}s to translate')
        
        translated_count = 0
        failed_count = 0
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = queryset[i:i + batch_size]
            
            for instance in batch:
                self.stdout.write(f'Translating {model_name}: {instance}')
                
                # Update status to processing
                if hasattr(instance, 'translation_status'):
                    instance.translation_status = 'processing'
                    instance.save()
                
                success = translation_service.translate_model_fields(instance, fields)
                
                if success:
                    translated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Translated: {instance}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed: {instance}')
                    )
                
                # Rate limiting to avoid API limits
                time.sleep(0.1)
            
            self.stdout.write(f'Completed batch {i//batch_size + 1}/{(total-1)//batch_size + 1}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Translation completed: {translated_count} successful, {failed_count} failed'
            )
        )