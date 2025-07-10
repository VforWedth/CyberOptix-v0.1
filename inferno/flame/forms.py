from django import forms
from flame.models import ProductReview

class ProductReviewForm(forms.ModelForm):
     review = forms.CharField(widget=forms.Textarea({'placeholder': "Write your review here..."}))
     
     class Meta:
         model = ProductReview
         fields = ['rating', 'review']
     