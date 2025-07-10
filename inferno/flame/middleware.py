from flame.models import User, Shop  # Replace 'your_app' with the actual app name where User and Shop are defined

class ShopAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.role == User.SHOP_ADMIN:
            request.session['shop_id'] = request.user.shop.id
        return self.get_response(request)
    
# # middleware.py
# class CartSanitizationMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if 'cart_data_obj' in request.session:
#             valid_shops = set(Shop.objects.values_list('shop_id', flat=True))
#             cart_data = request.session['cart_data_obj']
            
#             # Remove items from deleted shops
#             cart_data = {
#                 k: v for k, v in cart_data.items()
#                 if v.get('shop_id') in valid_shops
#             }
            
#             request.session['cart_data_obj'] = cart_data
#             request.session.modified = True

#         return self.get_response(request)