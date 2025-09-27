from django import forms
from flame.models import ProductReview, CartOrder,Product, ReviewReport, EmailTemplate, SocialMediaPost, Shop, MyanmarState, MyanmarCity, MyanmarTownship, ShippingRate
from django.utils.translation import gettext_lazy as _

class ProductReviewForm(forms.ModelForm):
    review = forms.CharField(widget=forms.Textarea({
        'placeholder': _("Write your review here..."),
        'class': 'form-control',
        'rows': 4
    }))
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-control'})
        }
        
class EnhancedProductReviewForm(forms.ModelForm):
    """Enhanced review form with detailed ratings"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Summary of your review")
        }),
        required=False
    )
    
    review = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _("Share your experience with this product...")
        })
    )
    
    rating = forms.ChoiceField(
        choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'})
    )
    
    quality_rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Quality Rating")
    )
    
    value_rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Value for Money")
    )
    
    delivery_rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Delivery Experience")
    )
    
    class Meta:
        model = ProductReview
        fields = ['title', 'review', 'rating', 'quality_rating', 'value_rating', 'delivery_rating']
    
    def clean(self):
        cleaned_data = super().clean()
        rating = cleaned_data.get('rating')
        review = cleaned_data.get('review')
        
        if rating and int(rating) <= 2 and not review:
            raise forms.ValidationError(_("Please provide a detailed review for low ratings."))
        
        return cleaned_data

class ReviewReportForm(forms.ModelForm):
    """Form for reporting inappropriate reviews"""
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Please explain why you're reporting this review...")
        }),
        required=False
    )
    
    class Meta:
        model = ReviewReport
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'})
        }

class EmailTemplateForm(forms.ModelForm):
    """Form for creating and editing email templates"""
    html_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': _("HTML content of the email template...")
        })
    )
    
    text_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': _("Plain text version (optional)...")
        }),
        required=False
    )
    
    class Meta:
        model = EmailTemplate
        fields = ['name', 'email_type', 'subject', 'html_content', 'text_content', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SocialMediaPostForm(forms.ModelForm):
    """Form for creating social media posts"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _("Write your social media post content...")
        })
    )
    
    scheduled_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        required=False,
        help_text=_("Leave blank to post immediately")
    )
    
    class Meta:
        model = SocialMediaPost
        fields = ['content', 'image_url', 'scheduled_at']
        widgets = {
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class BulkRestockForm(forms.Form):
    """Form for bulk restocking products"""
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text=_("Upload CSV file with columns: product_id, quantity, cost_per_unit")
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file and not file.name.endswith('.csv'):
            raise forms.ValidationError(_("Please upload a CSV file."))
        return file

class InventoryAdjustmentForm(forms.Form):
    """Form for inventory adjustments"""
    ADJUSTMENT_TYPES = (
        ('add', _('Add Stock')),
        ('remove', _('Remove Stock')),
        ('set', _('Set Stock Level')),
        ('damage', _('Mark as Damaged')),
    )
    
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    cost_per_unit = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Cost per unit (for restocking)")
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _("Reason for adjustment...")
        })
    )

class SearchForm(forms.Form):
    """Enhanced search form with filters"""
    q = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Search products...")
        }),
        required=False
    )
    
    category = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    brand = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('', _('Relevance')),
            ('-date', _('Newest First')),
            ('price', _('Price: Low to High')),
            ('-price', _('Price: High to Low')),
            ('-rating', _('Highest Rated')),
            ('-review_count', _('Most Reviewed')),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate category and brand choices
        from flame.models import Category, Brand
        
        category_choices = [('', _('All Categories'))]
        category_choices.extend([(c.id, c.title) for c in Category.objects.all()])
        self.fields['category'].choices = category_choices
        
        brand_choices = [('', _('All Brands'))]
        brand_choices.extend([(b.id, b.title) for b in Brand.objects.all()])
        self.fields['brand'].choices = brand_choices

class ShopLocationForm(forms.ModelForm):
    """Form for updating shop location"""
    state = forms.ModelChoiceField(
        queryset=MyanmarState.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'shop-state-select'
        }),
        empty_label=_("Select State/Region"),
        required=False
    )

    city = forms.ModelChoiceField(
        queryset=MyanmarCity.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'shop-city-select'
        }),
        empty_label=_("Select City"),
        required=False
    )

    township = forms.ModelChoiceField(
        queryset=MyanmarTownship.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'shop-township-select'
        }),
        empty_label=_("Select Township"),
        required=False
    )

    street_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Building number, street name, landmark...")
        }),
        required=False,
        help_text=_("Detailed address information")
    )

    class Meta:
        model = Shop
        fields = ['state', 'city', 'township', 'street_address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = MyanmarCity.objects.filter(state_id=state_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.state:
            self.fields['city'].queryset = self.instance.state.cities.all()

        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['township'].queryset = MyanmarTownship.objects.filter(city_id=city_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.city:
            self.fields['township'].queryset = self.instance.city.townships.all()

class ShippingRateForm(forms.ModelForm):
    """Form for managing shipping rates"""
    to_city = forms.ModelChoiceField(
        queryset=MyanmarCity.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        empty_label=_("Select Destination City")
    )

    rate_mmk = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("Rate in MMK"),
            'min': '0',
            'step': '0.01'
        }),
        help_text=_("Shipping rate in Myanmar Kyat")
    )

    rate_usd = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("Rate in USD"),
            'min': '0',
            'step': '0.01'
        }),
        help_text=_("Shipping rate in US Dollars")
    )

    estimated_days = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("Estimated delivery days"),
            'min': '1',
            'max': '30'
        }),
        help_text=_("Estimated delivery time in days")
    )

    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        initial=True,
        help_text=_("Enable this shipping option")
    )

    class Meta:
        model = ShippingRate
        fields = ['to_city', 'rate_mmk', 'rate_usd', 'estimated_days', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        rate_mmk = cleaned_data.get('rate_mmk')
        rate_usd = cleaned_data.get('rate_usd')

        if rate_mmk and rate_mmk <= 0:
            raise forms.ValidationError(_("MMK rate must be greater than zero"))

        if rate_usd and rate_usd <= 0:
            raise forms.ValidationError(_("USD rate must be greater than zero"))

        return cleaned_data


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
        exclude = ['user', 'p_id', 'sku', 'date', 'updated', 'last_translated', 'translation_status']

        fields = ['title', 'category', 'brand', 'shop', 'product_status', 'price', 'old_price',
                 'stock_count', 'featured', 'digital', 'image', 'description', 'specification',
                 'cpu', 'ram', 'display_currency_preference', 'in_stock', 'status',
                 'min_stock_level', 'max_stock_level']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'max_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-control'}),
            'shop': forms.Select(attrs={'class': 'form-control'}),
            'product_status': forms.Select(attrs={'class': 'form-control'}),
            'display_currency_preference': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'specification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cpu': forms.TextInput(attrs={'class': 'form-control'}),
            'ram': forms.TextInput(attrs={'class': 'form-control'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'digital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }