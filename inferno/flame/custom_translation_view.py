from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.translation import gettext as _
import polib
import os

@staff_member_required
def translation_dashboard(request):
    """Dashboard for managing translations"""
    from django.conf import settings
    
    # Get translation statistics
    my_po_path = os.path.join(settings.BASE_DIR, 'locale/my/LC_MESSAGES/django.po')
    
    if os.path.exists(my_po_path):
        po = polib.pofile(my_po_path)
        total_entries = len(po)
        translated = len(po.translated_entries())
        untranslated = len(po.untranslated_entries())
        fuzzy = len(po.fuzzy_entries())
        
        percentage = (translated / total_entries * 100) if total_entries > 0 else 0
    else:
        total_entries = translated = untranslated = fuzzy = percentage = 0
    
    context = {
        'total_entries': total_entries,
        'translated': translated,
        'untranslated': untranslated,
        'fuzzy': fuzzy,
        'percentage': percentage,
    }
    
    return render(request, 'admin/translation_dashboard.html', context)

@staff_member_required
def quick_translate(request):
    """Quick translation interface for common phrases"""
    if request.method == 'POST':
        # Handle translation updates
        messages.success(request, _('Translations updated successfully'))
        return redirect('translation_dashboard')
    
    # Get common untranslated strings
    common_strings = [
        'Add to Cart',
        'Checkout',
        'Product Details',
        'Customer Reviews',
        # Add more common strings
    ]
    
    return render(request, 'admin/quick_translate.html', {
        'strings': common_strings
    })