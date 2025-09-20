from django import forms
from flame.models import ProductReview,CartOrder,Product

class ProductReviewForm(forms.ModelForm):
     review = forms.CharField(widget=forms.Textarea({'placeholder': "Write your review here..."}))
     
     class Meta:
         model = ProductReview
         fields = ['rating', 'review']


class OrderForm(forms.ModelForm):
    class Meta:
        model = CartOrder
        exclude = ['user']   # 👈 don’t ask user in form
        fields = ['price', 'paid_status', 'product_status', 'shop', 'order_type']
        widgets = {
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # Add other widgets as needed
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['user','cpu','ram']   # 👈 don’t ask user in form

        fields = ['user','title','category','featured', 'price', 'brand','image','cpu','ram','description','specification', 'product_status', 'shop']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # Add other widgets as needed
        }