import json
import logging
from typing import Dict, Optional, List
from deep_translator import GoogleTranslator
from django.conf import settings
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.translator = GoogleTranslator()
        self.supported_languages = ['my', 'zh', 'th', 'vi']  # Add more as needed
        self.source_language = 'en'
    
    def translate_text(self, text: str, target_language: str) -> Optional[str]:
        """Translate single text to target language"""
        try:
            if not text or not text.strip():
                return ""
            
            result = self.translator.translate(
                text, 
                src=self.source_language, 
                dest=target_language
            )
            return result.text
        except Exception as e:
            logger.error(f"Translation error for '{text}' to '{target_language}': {e}")
            return None
    
    def translate_batch(self, texts: List[str], target_language: str) -> Dict[str, str]:
        """Translate multiple texts at once"""
        translations = {}
        for text in texts:
            if text:
                translated = self.translate_text(text, target_language)
                if translated:
                    translations[text] = translated
        return translations
    
    def translate_model_fields(self, instance, fields_to_translate: List[str]) -> bool:
        """Translate specified fields of a model instance"""
        try:
            with transaction.atomic():
                updated = False
                
                for language in self.supported_languages:
                    for field_name in fields_to_translate:
                        # Get original field value
                        original_value = getattr(instance, field_name, '')
                        
                        if not original_value:
                            continue
                        
                        # Get or create translation field
                        translation_field = f"{field_name}_translations"
                        if not hasattr(instance, translation_field):
                            continue
                        
                        translations = getattr(instance, translation_field) or {}
                        
                        # Skip if already translated
                        if language in translations and translations[language]:
                            continue
                        
                        # Translate
                        translated_text = self.translate_text(original_value, language)
                        if translated_text:
                            translations[language] = translated_text
                            setattr(instance, translation_field, translations)
                            updated = True
                
                if updated:
                    # Update translation metadata
                    if hasattr(instance, 'last_translated'):
                        instance.last_translated = timezone.now()
                    if hasattr(instance, 'translation_status'):
                        instance.translation_status = 'completed'
                    
                    instance.save()
                    logger.info(f"Successfully translated {instance.__class__.__name__} ID: {instance.id}")
                    return True
                    
        except Exception as e:
            logger.error(f"Translation failed for {instance.__class__.__name__} ID: {instance.id}: {e}")
            if hasattr(instance, 'translation_status'):
                instance.translation_status = 'failed'
                instance.save()
            return False
        
        return False

# Initialize service
translation_service = TranslationService()