from django.utils import timezone
from django.db import transaction
from flame.models import CartOrder, OrderStatusHistory, InventoryLog, EmailLog
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class OrderService:
    """Service class for managing order operations"""
    
    @staticmethod
    def update_order_status(order, new_status, user=None, notes="", location="", carrier=""):
        """Update order status and create history entry"""
        with transaction.atomic():
            old_status = order.product_status
            order.product_status = new_status
            
            # Update status timestamps
            current_time = timezone.now()
            if new_status == 'confirmed' and not order.confirmed_at:
                order.confirmed_at = current_time
            elif new_status == 'processing' and not order.processed_at:
                order.processed_at = current_time
            elif new_status == 'packed' and not order.packed_at:
                order.packed_at = current_time
            elif new_status == 'shipped' and not order.shipped_at:
                order.shipped_at = current_time
            elif new_status == 'delivered' and not order.delivered_at:
                order.delivered_at = current_time
                order.actual_delivery = current_time
            
            order.save()
            
            # Create status history entry
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=user,
                notes=notes,
                location=location,
                carrier=carrier
            )
            
            # Handle inventory updates for status changes
            if new_status == 'confirmed':
                OrderService._reserve_inventory(order)
            elif new_status == 'delivered':
                OrderService._fulfill_inventory(order)
            elif new_status == 'cancelled':
                OrderService._release_inventory(order)
            elif new_status == 'returned':
                OrderService._return_inventory(order)
            
            logger.info(f"Order {order.order_number} status updated from {old_status} to {new_status}")
            
            return order
    
    @staticmethod
    def _reserve_inventory(order):
        """Reserve inventory for confirmed order"""
        for item in order.cartorderitem_set.all():
            if item.product:
                success = item.product.reserve_stock(item.qty)
                if success:
                    InventoryLog.objects.create(
                        product=item.product,
                        action='reserve',
                        quantity=item.qty,
                        notes=f"Reserved for order {order.order_number}",
                        stock_after=item.product.stock_count,
                        reserved_after=item.product.reserved_stock
                    )
                else:
                    logger.warning(f"Failed to reserve {item.qty} units of {item.product.title} for order {order.order_number}")
    
    @staticmethod
    def _fulfill_inventory(order):
        """Fulfill inventory for delivered order"""
        for item in order.cartorderitem_set.all():
            if item.product:
                success = item.product.fulfill_order(item.qty)
                if success:
                    InventoryLog.objects.create(
                        product=item.product,
                        action='sale',
                        quantity=item.qty,
                        notes=f"Sold in order {order.order_number}",
                        stock_after=item.product.stock_count,
                        reserved_after=item.product.reserved_stock
                    )
    
    @staticmethod
    def _release_inventory(order):
        """Release inventory for cancelled order"""
        for item in order.cartorderitem_set.all():
            if item.product:
                item.product.release_reserved_stock(item.qty)
                InventoryLog.objects.create(
                    product=item.product,
                    action='release',
                    quantity=item.qty,
                    notes=f"Released from cancelled order {order.order_number}",
                    stock_after=item.product.stock_count,
                    reserved_after=item.product.reserved_stock
                )
    
    @staticmethod
    def _return_inventory(order):
        """Return inventory for returned order"""
        for item in order.cartorderitem_set.all():
            if item.product:
                item.product.restock(item.qty)
                InventoryLog.objects.create(
                    product=item.product,
                    action='return',
                    quantity=item.qty,
                    notes=f"Returned from order {order.order_number}",
                    stock_after=item.product.stock_count,
                    reserved_after=item.product.reserved_stock
                )
    
    @staticmethod
    def calculate_order_totals(order):
        """Calculate and update order totals"""
        subtotal = sum(item.total for item in order.cartorderitem_set.all())
        
        # Calculate tax (you can customize this logic)
        tax_rate = Decimal('0.05')  # 5% tax
        tax_amount = subtotal * tax_rate
        
        # Calculate shipping (you can customize this logic)
        shipping_cost = Decimal('10.00') if subtotal < Decimal('100.00') else Decimal('0.00')
        
        # Apply any discounts
        discount_amount = order.discount_amount or Decimal('0.00')
        
        total_amount = subtotal + tax_amount + shipping_cost - discount_amount
        
        order.price = subtotal
        order.tax_amount = tax_amount
        order.shipping_cost = shipping_cost
        order.total_amount = total_amount
        order.save()
        
        return order
    
    @staticmethod
    def get_order_tracking_info(order):
        """Get comprehensive tracking information for an order"""
        tracking_info = {
            'order': order,
            'progress_percentage': order.get_order_progress(),
            'status_history': order.status_history.all().order_by('-timestamp'),
            'can_cancel': order.can_be_cancelled(),
            'can_return': order.can_be_returned(),
            'estimated_delivery': order.estimated_delivery,
            'actual_delivery': order.actual_delivery,
            'tracking_number': order.tracking_number,
        }
        
        # Add current status info
        current_status = order.status_history.first()
        if current_status:
            tracking_info['current_location'] = current_status.location
            tracking_info['current_carrier'] = current_status.carrier
            tracking_info['last_update'] = current_status.timestamp
        
        return tracking_info
    
    @staticmethod
    def bulk_update_orders(orders, status, user=None, notes=""):
        """Bulk update multiple orders"""
        updated_count = 0
        for order in orders:
            try:
                OrderService.update_order_status(order, status, user, notes)
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update order {order.order_number}: {str(e)}")
        
        return updated_count
    
    @staticmethod
    def generate_tracking_number(order):
        """Generate a tracking number for an order"""
        import uuid
        tracking_number = f"TRK{order.id:06d}{uuid.uuid4().hex[:6].upper()}"
        order.tracking_number = tracking_number
        order.save()
        return tracking_number
    
    @staticmethod
    def estimate_delivery_date(order):
        """Estimate delivery date based on order details"""
        from datetime import timedelta
        
        # Basic delivery estimation logic (can be made more sophisticated)
        base_days = 3  # Standard delivery time
        
        # Add extra days for special conditions
        if order.order_type == 'home':
            base_days += 2
        
        if order.total_amount > Decimal('500.00'):
            base_days -= 1  # Faster delivery for high-value orders
        
        estimated_delivery = order.order_date + timedelta(days=base_days)
        order.estimated_delivery = estimated_delivery
        order.save()
        
        return estimated_delivery