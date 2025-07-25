from django.contrib.auth.models import User
from django.template.loader import render_to_string
from rest_framework import generics, status

from ashesi_offcampus_online_store_backend import settings
from ashesi_offcampus_online_store_backend.settings import EMAIL_HOST_PASSWORD
# from ashesi_offcampus_online_store_backend.settings import DEFAULT_FROM_EMAIL
from .serializers import UserProfileSerializer
from .models import FoodItems, UserProfile, Order
from .serializers import UserSerializer, FoodSerializer, OrderSerializer, OrderStatusSerializer
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
import requests
from django.conf import settings as django_settings

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
        current_site = get_current_site(request).domain
        verify_path  = reverse('email-verify')
        verify_url   = f"http://{current_site}{verify_path}?uid={uidb64}&token={token}"

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
