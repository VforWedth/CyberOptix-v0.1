from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from flame.models import EmailTemplate, EmailLog, User
from django.db import models
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for handling all notifications"""
    
    @staticmethod
    def send_order_notification(order, notification_type):
        """Send order-related notifications"""
        user = order.user
        if not user or not user.email:
            logger.warning(f"No email address for order {order.order_number}")
            return False
        
        template_mapping = {
            'confirmation': 'order_confirmation',
            'shipped': 'order_shipped',
            'delivered': 'order_delivered',
            'cancelled': 'order_cancelled',
        }
        
        email_type = template_mapping.get(notification_type)
        if not email_type:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        try:
            template = EmailTemplate.objects.get(email_type=email_type, is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template not found for type: {email_type}")
            return False
        
        context = NotificationService._get_order_context(order)
        
        return NotificationService._send_email(
            template=template,
            user=user,
            context=context,
            context_data={'order_id': order.id}
        )
    
    @staticmethod
    def send_inventory_alert(product, alert_type):
        """Send inventory-related alerts to administrators"""
        admin_users = User.objects.filter(is_superuser=True, is_active=True)
        
        template_mapping = {
            'low_stock': 'low_stock',
            'out_of_stock': 'out_of_stock',
            'restock_needed': 'restock_needed',
        }
        
        email_type = template_mapping.get(alert_type)
        if not email_type:
            logger.error(f"Unknown alert type: {alert_type}")
            return False
        
        try:
            template = EmailTemplate.objects.get(email_type=email_type, is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template not found for type: {email_type}")
            return False
        
        sent_count = 0
        for admin in admin_users:
            context = {
                'user_name': admin.username,
                'product': product,
                'available_stock': product.get_available_stock(),
                'min_stock_level': product.min_stock_level,
                'site_name': 'CyberOptix',
            }
            
            if NotificationService._send_email(
                template=template,
                user=admin,
                context=context,
                context_data={'product_id': product.id}
            ):
                sent_count += 1
        
        return sent_count > 0
    
    @staticmethod
    def send_review_request(order):
        """Send review request email to customer"""
        user = order.user
        if not user or not user.email:
            return False
        
        # Check if review request already sent for this order
        if EmailLog.objects.filter(
            user=user,
            email_type='review_request',
            context_data__order_id=order.id
        ).exists():
            return False
        
        try:
            template = EmailTemplate.objects.get(email_type='review_request', is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error("Review request email template not found")
            return False
        
        context = NotificationService._get_order_context(order)
        context['review_deadline'] = (timezone.now() + timezone.timedelta(days=30)).date()
        
        return NotificationService._send_email(
            template=template,
            user=user,
            context=context,
            context_data={'order_id': order.id}
        )
    
    @staticmethod
    def send_promotional_email(users, template_name, context_data=None):
        """Send promotional emails to a list of users"""
        try:
            template = EmailTemplate.objects.get(email_type='promotional', name=template_name, is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error(f"Promotional email template '{template_name}' not found")
            return 0
        
        sent_count = 0
        for user in users:
            if not user.email:
                continue
            
            context = {
                'user_name': user.username,
                'site_name': 'CyberOptix',
                'unsubscribe_url': f"/unsubscribe/{user.id}/",  # You'd implement this
            }
            
            if context_data:
                context.update(context_data)
            
            if NotificationService._send_email(
                template=template,
                user=user,
                context=context,
                context_data={'template_name': template_name}
            ):
                sent_count += 1
        
        return sent_count
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        try:
            template = EmailTemplate.objects.get(email_type='welcome', is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.error("Welcome email template not found")
            return False
        
        context = {
            'user_name': user.username,
            'site_name': 'CyberOptix',
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://cyberoptix.com',
            'login_url': '/user/sign-in/',
        }
        
        return NotificationService._send_email(
            template=template,
            user=user,
            context=context,
            context_data={'welcome': True}
        )
    
    @staticmethod
    def _get_order_context(order):
        """Get common context data for order emails"""
        return {
            'user_name': order.user.username,
            'order_number': order.order_number,
            'order_date': order.order_date,
            'order_total': order.total_amount,
            'order_items': order.cartorderitem_set.all(),
            'tracking_number': order.tracking_number,
            'estimated_delivery': order.estimated_delivery,
            'actual_delivery': order.actual_delivery,
            'delivery_address': order.delivery_address,
            'site_name': 'CyberOptix',
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'order_url': f"/orders/{order.id}/",  # You'd implement this view
        }
    
    @staticmethod
    def _send_email(template, user, context, context_data=None):
        """Internal method to send email using template"""
        try:
            # Render email content
            html_content = NotificationService._render_template(template.html_content, context)
            text_content = template.text_content or strip_tags(html_content)
            
            # Create email log
            email_log = EmailLog.objects.create(
                user=user,
                email_template=template,
                email_type=template.email_type,
                recipient_email=user.email,
                subject=template.subject,
                status='pending',
                context_data=context_data or {}
            )
            
            # Send email
            send_mail(
                subject=template.subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            # Update log status
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save()
            
            logger.info(f"Email sent successfully to {user.email} (type: {template.email_type})")
            return True
            
        except Exception as e:
            # Update log with error
            if 'email_log' in locals():
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
            
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def _render_template(template_content, context):
        """Render email template with context"""
        from django.template import Template, Context
        template = Template(template_content)
        return template.render(Context(context))
    
    @staticmethod
    def get_email_statistics(days=30):
        """Get email sending statistics for the last N days"""
        from django.db.models import Count
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        stats = EmailLog.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            total_emails=Count('id'),
            sent_emails=Count('id', filter=models.Q(status='sent')),
            failed_emails=Count('id', filter=models.Q(status='failed')),
            delivered_emails=Count('id', filter=models.Q(status='delivered')),
            opened_emails=Count('id', filter=models.Q(opened_at__isnull=False)),
            clicked_emails=Count('id', filter=models.Q(clicked_at__isnull=False)),
        )
        
        # Calculate rates
        total = stats['total_emails'] or 1
        stats['delivery_rate'] = (stats['sent_emails'] / total) * 100
        stats['failure_rate'] = (stats['failed_emails'] / total) * 100
        
        if stats['sent_emails']:
            stats['open_rate'] = (stats['opened_emails'] / stats['sent_emails']) * 100
            stats['click_rate'] = (stats['clicked_emails'] / stats['sent_emails']) * 100
        else:
            stats['open_rate'] = 0
            stats['click_rate'] = 0
        
        return stats