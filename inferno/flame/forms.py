from django import forms
from flame.models import ProductReview
from django.utils.translation import gettext_lazy as _

class ProductReviewForm(forms.ModelForm):
     review = forms.CharField(widget=forms.Textarea({'placeholder': _("Write your review here...")}))
     
     class Meta:
         model = ProductReview
         fields = ['rating', 'review']
     