from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user                  = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number          = models.CharField(max_length=20)
    hostel_or_office_name = models.CharField(max_length=255)
    room_or_office_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user} profile"


class FoodItems(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.TextField()
    status = models.BooleanField(default=False)
    extras = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_RECEIVED        = 'RECEIVED'
    STATUS_PREPARING       = 'PREPARING'
    STATUS_OUT_FOR_DELIVERY= 'OUT_FOR_DELIVERY'
    STATUS_DELIVERED       = 'DELIVERED'

    STATUS_CHOICES = [
        (STATUS_RECEIVED,         'Order Received'),
        (STATUS_PREPARING,        'Order is being prepared'),
        (STATUS_OUT_FOR_DELIVERY, 'Order out for delivery'),
        (STATUS_DELIVERED,        'Delivered'),
    ]

    user        = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.CASCADE,
                     related_name='orders'
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status      = models.CharField(
                     max_length=20,
                     choices=STATUS_CHOICES,
                     default=STATUS_RECEIVED
                  )

    def __str__(self):
        return f"Order {self.id} ({self.get_status_display()})"


class OrderItem(models.Model):
    order     = models.ForeignKey(
                   Order,
                   on_delete=models.CASCADE,
                   related_name='items'
                )
    food_item = models.ForeignKey('FoodItems', on_delete=models.CASCADE)
    quantity  = models.PositiveIntegerField(default=1)
    price     = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # auto-compute line price if not explicitly set
        if not self.price:
            self.price = self.food_item.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}× {self.food_item.name} (Order {self.order.id})"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("card", "Card"),
        ("momo", "Mobile Money"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    paystack_reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} ({self.status})"
