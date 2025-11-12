from django.contrib.auth.models import User
from django.template.loader import render_to_string
from rest_framework import generics, status

from ashesi_offcampus_online_store_backend import settings
from ashesi_offcampus_online_store_backend.settings import EMAIL_HOST_PASSWORD
from .serializers import UserProfileSerializer
from .models import FoodItems, UserProfile, Order, OrderItem
from .serializers import (
    UserSerializer,
    FoodSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    OrderUpdateSerializer,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect

from .serializers import PasswordResetSerializer
from .models import Payment
from .serializers import PaymentInitiateSerializer
from .permissions import IsSuperAdmin, IsStaffMember
import requests
from django.conf import settings as django_settings
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import datetime, time
from rest_framework.exceptions import PermissionDenied, ValidationError

# Create your views here.
# request --> response. So we will say it is a request handler.




class CreateUserView(generics.CreateAPIView):
    """
    1) Creates user (inactive) + profile
    2) Sends verification email
    """
    queryset            = User.objects.all()
    serializer_class    = UserSerializer
    authentication_classes = []
    permission_classes  = [AllowAny]

    def create(self, request, *args, **kwargs):
        # a) validate & save (user.is_active=False in serializer.create)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # b) build the one‑time link
        uidb64       = urlsafe_base64_encode(force_bytes(user.pk))
        token        = default_token_generator.make_token(user)
        verify_path  = reverse('email-verify')
        # Use request scheme and host for production compatibility (handles HTTPS)
        scheme = 'https' if not django_settings.DEBUG else request.scheme
        current_site = get_current_site(request).domain
        verify_url   = f"{scheme}://{current_site}{verify_path}?uid={uidb64}&token={token}"

        # c) send it
        email_body = (
            f"Hi {user.username},\n\n"
            "Thanks for registering at Ashesi Off-campus Online Shop.\n"
            "Please click the link below to verify your email address:\n\n"
            f"{verify_url}\n\n"
            "If you didn't register, you can safely ignore this email.\n"
        )
        msg = EmailMessage(
            subject    = "Verify your email",
            body       = email_body,
            to         = [user.email],
        )
        msg.encoding = 'utf-8'
        msg.send(fail_silently=False)

        return Response(
            {"detail": "Registration successful. Check your email for a verification link."},
            status=status.HTTP_201_CREATED
        )


class VerifyEmail(APIView):
    """
    GET /api/email-verify/?uid=…&token=…
      → activates the account and redirects to your React login page
    """
    permission_classes = [AllowAny]

    def get(self, request):
        uidb64 = request.GET.get('uid')
        token  = request.GET.get('token')

        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            # redirect into your React app's signup route using settings with verified parameter:
            return redirect(f"{django_settings.FRONTEND_URL}/signup?verified=true")
        return Response(
            {"error": "Invalid or expired verification link."},
            status=status.HTTP_400_BAD_REQUEST
        )

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/user/profile/  → fetch all fields (username read-only)
    PATCH /api/user/profile/ → update any subset of fields
    """
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class PasswordResetView(generics.GenericAPIView):
    """
    POST /api/password-reset/
      • { email }                                  → 200 if email exists, 404 if not
      • { email, new_password, confirm_password }  → 200 on success, 400 on validation error
    """
    serializer_class    = PasswordResetSerializer
    permission_classes  = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # this will run both email‐exists and password validations
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        # if only email was provided, prompt front‑end to show password fields
        if 'new_password' not in data:
            return Response(
                {"detail": "Email exists. Please enter your new password."},
                status=status.HTTP_200_OK
            )

        # otherwise, actually reset the password
        serializer.save()
        return Response(
            {"detail": "Password has been reset. You may now log in."},
            status=status.HTTP_200_OK
        )


class FoodListView(generics.ListAPIView):
    queryset = FoodItems.objects.filter(status=True)
    serializer_class = FoodSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


class FoodAdminListCreateView(generics.ListCreateAPIView):
    queryset = FoodItems.objects.all().order_by('name')
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class FoodAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FoodItems.objects.all()
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/orders/  → list all orders for the logged-in user
    POST /api/orders/  → create a new order (with nested items)
    """
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only your own orders
        return Order.objects.filter(user=self.request.user).prefetch_related('items__food_item')

    def perform_create(self, serializer):
        # attach the user context so serializer.create() can read it
        serializer.save()


class StaffOrderListView(generics.ListAPIView):
    """
    GET /api/orders/manage/ → list all orders for staff (super admin, employee, cook)
    Supports optional filtering by status (?status=RECEIVED).
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsStaffMember]

    def get_queryset(self):
        queryset = Order.objects.all().prefetch_related('items__food_item', 'user__userprofile').order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/orders/<id>/    → retrieve a specific order
    PATCH  /api/orders/<id>/    → update status (currently)
    DELETE /api/orders/<id>/    → remove order (used when payment fails)
    """
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        queryset = Order.objects.all().prefetch_related('items__food_item')
        try:
            role = self.request.user.userprofile.role
        except UserProfile.DoesNotExist:
            role = None
        if role in [UserProfile.ROLE_SUPER_ADMIN, UserProfile.ROLE_EMPLOYEE, UserProfile.ROLE_COOK]:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return OrderUpdateSerializer
        return OrderSerializer

    def perform_update(self, serializer):
        validated_data = dict(serializer.validated_data)
        try:
            role = self.request.user.userprofile.role
        except UserProfile.DoesNotExist:
            role = None
        if 'status' in validated_data and role not in [UserProfile.ROLE_SUPER_ADMIN, UserProfile.ROLE_EMPLOYEE, UserProfile.ROLE_COOK]:
            raise PermissionDenied("You do not have permission to update order status.")
        serializer.save()





class OrderStatusView(generics.RetrieveAPIView):
    """
    GET /api/orders/<order_id>/status/
    → 200 { "id": 123, "status": "PREPARING" }
    """
    serializer_class   = OrderStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg   = 'order_id'

    def get_object(self):
        # only allow the owner to fetch
        return get_object_or_404(
            Order,
            id=self.kwargs['order_id'],
            user=self.request.user
        )

class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        order = data["order"]
        amount = int(float(data["amount"]) * 100)  # Paystack expects amount in kobo/pesewas
        payment_method = data["payment_method"]
        email = data["email"]
        phone = data.get("phone", "")

        # Prepare Paystack payload
        paystack_data = {
            "amount": amount,
            "email": email,
            "currency": "GHS",
            # Set callback_url to frontend payment-complete page using settings
            "callback_url": f"{django_settings.FRONTEND_URL}/payment/verify",
        }
        if payment_method == "momo":
            paystack_data["channels"] = ["mobile_money"]
            paystack_data["mobile_money"] = {"phone": phone, "provider": "mtn"}  # Only MTN for now
        else:
            paystack_data["channels"] = ["card"]

        headers = {
            "Authorization": f"Bearer {django_settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.post(f"{django_settings.PAYSTACK_BASE_URL}/transaction/initialize", json=paystack_data, headers=headers)
        resp_json = response.json()
        if not resp_json.get("status"):
            return Response({"error": resp_json.get("message", "Paystack error")}, status=400)
        paystack_ref = resp_json["data"]["reference"]
        payment_url = resp_json["data"]["authorization_url"]

        # Create Payment record
        Payment.objects.create(
            user=user,
            order=order,
            amount=data["amount"],
            payment_method=payment_method,
            status="pending",
            paystack_reference=paystack_ref,
        )
        return Response({"payment_url": payment_url, "reference": paystack_ref})

class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"error": "Reference is required."}, status=400)
        try:
            payment = Payment.objects.get(paystack_reference=reference, user=request.user)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=404)
        headers = {
            "Authorization": f"Bearer {django_settings.PAYSTACK_SECRET_KEY}",
        }
        verify_url = f"{django_settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"
        resp = requests.get(verify_url, headers=headers)
        resp_json = resp.json()
        if resp_json.get("status") and resp_json["data"]["status"] == "success":
            payment.status = "success"
            payment.save()
            payment.order.status = Order.STATUS_RECEIVED  # or update as needed
            payment.order.save()
            return Response({"status": "success"})
        else:
            payment.status = "failed"
            payment.save()
            return Response({"status": "failed", "message": resp_json.get("message", "Payment failed.")}, status=400)


class DashboardSummaryView(APIView):
    """
    GET /api/dashboard/summary/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    Returns total sales and top-performing menu items within the date range.
    Defaults to the current day if no dates are supplied.
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        current_tz = timezone.get_current_timezone()
        today = timezone.localdate()

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError({"start_date": "Invalid date format. Use YYYY-MM-DD."})
        else:
            start_date = today

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError({"end_date": "Invalid date format. Use YYYY-MM-DD."})
        else:
            end_date = start_date

        if end_date < start_date:
            raise ValidationError({"detail": "end_date cannot be earlier than start_date."})

        start_dt = timezone.make_aware(datetime.combine(start_date, time.min), current_tz)
        end_dt = timezone.make_aware(datetime.combine(end_date, time.max), current_tz)

        orders = (
            Order.objects.filter(
                created_at__range=(start_dt, end_dt),
                payments__status="success",
                status=Order.STATUS_DELIVERED,
            ).distinct()
        )

        totals = orders.aggregate(
            total_sales=Sum('total_price'),
            average_order_value=Avg('total_price'),
        )

        total_sales = totals.get('total_sales') or 0
        average_order_value = totals.get('average_order_value') or 0
        total_orders = orders.count()

        top_items_queryset = (
            OrderItem.objects.filter(order__in=orders)
            .values('food_item__id', 'food_item__name')
            .annotate(
                quantity_sold=Sum('quantity'),
                revenue=Sum('price'),
            )
            .order_by('-quantity_sold')[:5]
        )

        top_items = [
            {
                "food_item_id": item['food_item__id'],
                "name": item['food_item__name'],
                "quantity_sold": item['quantity_sold'],
                "revenue": item['revenue'],
            }
            for item in top_items_queryset
        ]

        return Response(
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_sales": total_sales,
                "total_orders": total_orders,
                "average_order_value": average_order_value,
                "top_items": top_items,
            }
        )
