from django.urls import path
from . import views
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderStatusView,
    PasswordResetView,
    PaymentInitiateView,
    PaymentVerifyView,
    FoodAdminListCreateView,
    FoodAdminDetailView,
    StaffOrderListView,
    DashboardSummaryView,
)

urlpatterns = [
    path("foodItems/", views.FoodListView.as_view(), name="foodItem-list"),
    path("foodItems/manage/", FoodAdminListCreateView.as_view(), name="foodItem-manage"),
    path("foodItems/manage/<int:pk>/", FoodAdminDetailView.as_view(), name="foodItem-manage-detail"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/manage/', StaffOrderListView.as_view(), name='order-manage'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/status/', OrderStatusView.as_view(), name='order-status'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('payments/initiate/', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]