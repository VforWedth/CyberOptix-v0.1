from django.urls import path
from . import views

app_name = 'kbzpay_mock'

urlpatterns = [
    # Mock KBZPay API endpoints
    path('api/precreate/', views.mock_precreate, name='mock_precreate'),
    path('api/query/', views.mock_query_status, name='mock_query_status'),

    # Mock payment confirmation page
    path('payment/<str:prepay_id>/', views.mock_payment_page, name='mock_payment_page'),

    # Testing endpoint to simulate successful payment
    path('simulate/success/<str:prepay_id>/', views.simulate_payment_success, name='simulate_success'),
]