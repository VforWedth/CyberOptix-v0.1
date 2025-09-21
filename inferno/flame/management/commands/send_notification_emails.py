from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from flame.models import (
    CartOrder, Product, EmailTemplate, EmailLog, User,
    OrderStatusHistory
)
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send automated notification emails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['order_confirmation', 'order_shipped', 'order_delivered', 'low_stock', 'abandoned_cart', 'review_request'],
            help='Type of email to send'
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to specific email address'
        )
    
    def handle(self, *args, **options):
        email_type = options.get('type')
        test_email = options.get('test_email')
        
        if test_email:
            self.send_test_email(test_email)
            return
        
        if email_type:
            if email_type == 'order_confirmation':
                self.send_order_confirmations()
            elif email_type == 'order_shipped':
                self.send_order_shipped_notifications()
            elif email_type == 'order_delivered':
                self.send_order_delivered_notifications()
            elif email_type == 'low_stock':
                self.send_low_stock_alerts()
            elif email_type == 'abandoned_cart':
                self.send_abandoned_cart_emails()
            elif email_type == 'review_request':
                self.send_review_requests()
        else:
            # Send all types
            self.send_order_confirmations()
            self.send_order_shipped_notifications()
            self.send_order_delivered_notifications()
            self.send_low_stock_alerts()
            self.send_abandoned_cart_emails()
            self.send_review_requests()
        
        self.stdout.write(
            self.style.SUCCESS('Email notifications sent successfully')
        )
    
    def send_test_email(self, email):
        """Send a test email"""
        try:
            template = EmailTemplate.objects.get(email_type='welcome')
            
            context = {
                'user_name': 'Test User',
                'site_name': 'CyberOptix',
                'site_url': 'https://cyberoptix.com',
            }
            
            html_content = self.render_email_template(template.html_content, context)
            text_content = strip_tags(html_content)
            
            send_mail(
                subject='Test Email - ' + template.subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent to {email}')
            )
            
        except EmailTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Welcome email template not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send test email: {str(e)}')
            )
    
    def send_order_confirmations(self):
        """Send order confirmation emails for recent orders"""
        # Find orders confirmed in the last hour that haven't been emailed
        recent_orders = CartOrder.objects.filter(
            confirmed_at__gte=timezone.now() - timedelta(hours=1),
            confirmed_at__isnull=False
        ).exclude(
            emaillog__email_type='order_confirmation',
            emaillog__status__in=['sent', 'delivered']
        )
        
        template = self.get_email_template('order_confirmation')
        if not template:
            return
        
        for order in recent_orders:
            try:
                context = {
                    'user_name': order.user.username,
                    'order_number': order.order_number,
                    'order_total': order.total_amount,
                    'order_items': order.cartorderitem_set.all(),
                    'estimated_delivery': order.estimated_delivery,
                    'site_name': 'CyberOptix',
                }
                
                self.send_email(
                    template=template,
                    user=order.user,
                    context=context,
                    context_data={'order_id': order.id}
                )
                
            except Exception as e:
                logger.error(f"Failed to send order confirmation for order {order.order_number}: {str(e)}")
    
    def send_order_shipped_notifications(self):
        """Send notifications when orders are shipped"""
        # Find orders shipped in the last hour
        recent_shipments = CartOrder.objects.filter(
            shipped_at__gte=timezone.now() - timedelta(hours=1),
            shipped_at__isnull=False
        ).exclude(
            emaillog__email_type='order_shipped',
            emaillog__status__in=['sent', 'delivered']
        )
        
        template = self.get_email_template('order_shipped')
        if not template:
            return
        
        for order in recent_shipments:
            try:
                context = {
                    'user_name': order.user.username,
                    'order_number': order.order_number,
                    'tracking_number': order.tracking_number,
                    'estimated_delivery': order.estimated_delivery,
                    'site_name': 'CyberOptix',
                }
                
                self.send_email(
                    template=template,
                    user=order.user,
                    context=context,
                    context_data={'order_id': order.id}
                )
                
            except Exception as e:
                logger.error(f"Failed to send shipping notification for order {order.order_number}: {str(e)}")
    
    def send_order_delivered_notifications(self):
        """Send notifications when orders are delivered"""
        recent_deliveries = CartOrder.objects.filter(
            delivered_at__gte=timezone.now() - timedelta(hours=1),
            delivered_at__isnull=False
        ).exclude(
            emaillog__email_type='order_delivered',
            emaillog__status__in=['sent', 'delivered']
        )
        
        template = self.get_email_template('order_delivered')
        if not template:
            return
        
        for order in recent_deliveries:
            try:
                context = {
                    'user_name': order.user.username,
                    'order_number': order.order_number,
                    'delivered_date': order.delivered_at,
                    'site_name': 'CyberOptix',
                }
                
                self.send_email(
                    template=template,
                    user=order.user,
                    context=context,
                    context_data={'order_id': order.id}
                )
                
            except Exception as e:
                logger.error(f"Failed to send delivery notification for order {order.order_number}: {str(e)}")
    
    def send_low_stock_alerts(self):
        """Send low stock alerts to admins"""
        low_stock_products = Product.objects.filter(
            status=True,
            stock_count__lte=F('min_stock_level')
        ).exclude(
            emaillog__email_type='low_stock',
            emaillog__created_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        if not low_stock_products:
            return
        
        template = self.get_email_template('low_stock')
        if not template:
            return
        
        # Send to all superusers
        admin_users = User.objects.filter(is_superuser=True, is_active=True)
        
        for admin_user in admin_users:
            try:
                context = {
                    'user_name': admin_user.username,
                    'low_stock_products': low_stock_products,
                    'site_name': 'CyberOptix',
                }
                
                self.send_email(
                    template=template,
                    user=admin_user,
                    context=context,
                    context_data={'product_count': low_stock_products.count()}
                )
                
            except Exception as e:
                logger.error(f"Failed to send low stock alert to {admin_user.username}: {str(e)}")
    
    def send_abandoned_cart_emails(self):
        """Send abandoned cart recovery emails"""
        # This would typically be implemented with a cart session tracking system
        # For now, we'll skip this as it requires more complex session management
        pass
    
    def send_review_requests(self):
        """Send review request emails for delivered orders"""
        # Find orders delivered 3 days ago that haven't been reviewed
        target_date = timezone.now() - timedelta(days=3)
        eligible_orders = CartOrder.objects.filter(
            delivered_at__date=target_date.date(),
            product_status='delivered'
        ).exclude(
            cartorderitem__product__reviews__user=F('user')
        ).exclude(
            emaillog__email_type='review_request',
            emaillog__status__in=['sent', 'delivered']
        )
        
        template = self.get_email_template('review_request')
        if not template:
            return
        
        for order in eligible_orders:
            try:
                context = {
                    'user_name': order.user.username,
                    'order_number': order.order_number,
                    'order_items': order.cartorderitem_set.all(),
                    'site_name': 'CyberOptix',
                }
                
                self.send_email(
                    template=template,
                    user=order.user,
                    context=context,
                    context_data={'order_id': order.id}
                )
                
            except Exception as e:
                logger.error(f"Failed to send review request for order {order.order_number}: {str(e)}")
    
    def get_email_template(self, email_type):
        """Get email template by type"""
        try:
            return EmailTemplate.objects.get(email_type=email_type, is_active=True)
        except EmailTemplate.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'Email template for {email_type} not found')
            )
            return None
    
    def render_email_template(self, template_content, context):
        """Render email template with context"""
        from django.template import Template, Context
        template = Template(template_content)
        return template.render(Context(context))
    
    def send_email(self, template, user, context, context_data=None):
        """Send email using template"""
        html_content = self.render_email_template(template.html_content, context)
        text_content = template.text_content or strip_tags(html_content)
        
        # Log email attempt
        email_log = EmailLog.objects.create(
            user=user,
            email_template=template,
            email_type=template.email_type,
            recipient_email=user.email,
            subject=template.subject,
            status='pending',
            context_data=context_data or {}
        )
        
        try:
            send_mail(
                subject=template.subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            # Update email log status
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            logger.info(f"Email sent successfully to {user.email}")
            
        except Exception as e:
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.save()
            
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            raise