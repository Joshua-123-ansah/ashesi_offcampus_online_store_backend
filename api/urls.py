from django.urls import path
from . import views
from .views import OrderListCreateView, OrderStatusView, PasswordResetView, PaymentInitiateView, PaymentVerifyView

urlpatterns = [
    path("foodItems/", views.FoodListView.as_view(), name="foodItem-list"),
    path("profile/" , views.UserProfileView.as_view(), name="profile"),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path(
          'orders/<int:order_id>/status/',
          OrderStatusView.as_view(),
          name='order-status'
        ),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('payments/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
]