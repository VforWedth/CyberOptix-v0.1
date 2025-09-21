from modeltranslation.translator import translator, TranslationOptions
from .models import (
    Product, Category, Brand, Shop, 
    ProductReview, CartOrder, CartOrderItem
)

class CategoryTranslationOptions(TranslationOptions):
    fields = ('title',)
    required_languages = ('en',)  # English is required
    
class BrandTranslationOptions(TranslationOptions):
    fields = ('title',)
    required_languages = ('en',)

class ShopTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'address')
    required_languages = ('en',)

class ProductTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'specification', 'cpu', 'ram')
    required_languages = ('en',)
    fallback_languages = {'default': ('en',)}

# Register translations
translator.register(Category, CategoryTranslationOptions)
translator.register(Brand, BrandTranslationOptions)
translator.register(Shop, ShopTranslationOptions)
translator.register(Product, ProductTranslationOptions)