from django.core.management.base import BaseCommand
from flame.models import EmailTemplate

class Command(BaseCommand):
    help = 'Create default email templates'
    
    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Order Confirmation',
                'email_type': 'order_confirmation',
                'subject': 'Order Confirmed - {{ order_number }}',
                'html_content': '''
                <h2>Order Confirmation</h2>
                <p>Dear {{ user_name }},</p>
                <p>Thank you for your order! Your order <strong>{{ order_number }}</strong> has been confirmed.</p>
                <p><strong>Order Details:</strong></p>
                <p>Total: ${{ order_total }}</p>
                {% if estimated_delivery %}
                <p>Estimated Delivery: {{ estimated_delivery }}</p>
                {% endif %}
                <p>You can track your order status at any time on our website.</p>
                <p>Best regards,<br>{{ site_name }} Team</p>
                ''',
                'text_content': '''
                Order Confirmation
                
                Dear {{ user_name }},
                
                Thank you for your order! Your order {{ order_number }} has been confirmed.
                
                Order Details:
                Total: ${{ order_total }}
                {% if estimated_delivery %}Estimated Delivery: {{ estimated_delivery }}{% endif %}
                
                You can track your order status at any time on our website.
                
                Best regards,
                {{ site_name }} Team
                '''
            },
            {
                'name': 'Order Shipped',
                'email_type': 'order_shipped',
                'subject': 'Your Order Has Shipped - {{ order_number }}',
                'html_content': '''
                <h2>Your Order Has Shipped!</h2>
                <p>Dear {{ user_name }},</p>
                <p>Great news! Your order <strong>{{ order_number }}</strong> has been shipped.</p>
                {% if tracking_number %}
                <p><strong>Tracking Number:</strong> {{ tracking_number }}</p>
                {% endif %}
                {% if estimated_delivery %}
                <p><strong>Estimated Delivery:</strong> {{ estimated_delivery }}</p>
                {% endif %}
                <p>You can track your package using the tracking number above.</p>
                <p>Best regards,<br>{{ site_name }} Team</p>
                ''',
            },
            {
                'name': 'Low Stock Alert',
                'email_type': 'low_stock',
                'subject': 'Low Stock Alert - Action Required',
                'html_content': '''
                <h2>Low Stock Alert</h2>
                <p>Dear {{ user_name }},</p>
                <p>The following products are running low on stock:</p>
                {% for product in low_stock_products %}
                <p><strong>{{ product.title }}</strong> - Only {{ product.get_available_stock }} remaining</p>
                {% endfor %}
                <p>Please restock these items as soon as possible.</p>
                <p>Best regards,<br>{{ site_name }} System</p>
                ''',
            },
            {
                'name': 'Review Request',
                'email_type': 'review_request',
                'subject': 'How was your recent purchase?',
                'html_content': '''
                <h2>How was your recent purchase?</h2>
                <p>Dear {{ user_name }},</p>
                <p>We hope you're enjoying your recent purchase from order {{ order_number }}!</p>
                <p>Your feedback is important to us and helps other customers make informed decisions.</p>
                <p>Would you mind taking a moment to review your purchase?</p>
                <p><a href="{{ site_url }}/orders/{{ order.id }}/">Leave a Review</a></p>
                <p>Thank you for choosing {{ site_name }}!</p>
                <p>Best regards,<br>{{ site_name }} Team</p>
                ''',
            },
            {
                'name': 'Welcome Email',
                'email_type': 'welcome',
                'subject': 'Welcome to {{ site_name }}!',
                'html_content': '''
                <h2>Welcome to {{ site_name }}!</h2>
                <p>Dear {{ user_name }},</p>
                <p>Thank you for joining {{ site_name }}! We're excited to have you as part of our community.</p>
                <p>Here's what you can do with your account:</p>
                <ul>
                    <li>Browse our extensive product catalog</li>
                    <li>Track your orders in real-time</li>
                    <li>Save items to your wishlist</li>
                    <li>Leave reviews and ratings</li>
                    <li>Get personalized recommendations</li>
                </ul>
                <p>Get started by exploring our products!</p>
                <p><a href="{{ site_url }}">Start Shopping</a></p>
                <p>Best regards,<br>{{ site_name }} Team</p>
                ''',
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                email_type=template_data['email_type'],
                defaults={
                    'subject': template_data['subject'],
                    'html_content': template_data['html_content'],
                    'text_content': template_data.get('text_content', ''),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} email templates')
        )