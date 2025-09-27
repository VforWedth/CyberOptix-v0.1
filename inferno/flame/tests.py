# Create tests/test_translation.py
from django.test import TestCase, Client
from django.utils import translation
from django.urls import reverse

class TranslationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_language_switching(self):
        """Test language switching functionality"""
        # Test English
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='en')
        self.assertContains(response, 'Home')
        
        # Test Myanmar
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='my')
        self.assertContains(response, 'ပင်မစာမျက်နှာ')
    
    def test_model_translation(self):
        """Test model field translations"""
        from flame.models import Category
        
        category = Category.objects.create(
            title_en='Laptop',
            title_my='လက်ပ်တော့'
        )
        
        with translation.override('en'):
            self.assertEqual(category.title, 'Laptop')
        
        with translation.override('my'):
            self.assertEqual(category.title, 'လက်ပ်တော့')