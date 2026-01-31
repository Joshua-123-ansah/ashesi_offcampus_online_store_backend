from django.conf import settings
from django.db import models


class Shop(models.Model):
    """Shop model representing different stores in the platform"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)  # URL to shop image
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_SHOP_MANAGER = 'shop_manager'
    ROLE_EMPLOYEE    = 'employee'
    ROLE_COOK        = 'cook'
    ROLE_STUDENT     = 'student'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin'),
        (ROLE_SHOP_MANAGER, 'Shop Manager'),
        (ROLE_EMPLOYEE,    'Employee'),
        (ROLE_COOK,        'Cook'),
        (ROLE_STUDENT,     'Student'),
    ]

    user                  = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number          = models.CharField(max_length=20)
    hostel_or_office_name = models.CharField(max_length=255)
    room_or_office_number = models.CharField(max_length=50)
    role                  = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    shop                  = models.ForeignKey('Shop', on_delete=models.SET_NULL, null=True, blank=True, related_name='managers')

    def __str__(self):
        return f"{self.user} profile ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN

    @property
    def is_staff_role(self):
        return self.role in {self.ROLE_SUPER_ADMIN, self.ROLE_SHOP_MANAGER, self.ROLE_EMPLOYEE, self.ROLE_COOK}
    
    @property
    def is_shop_manager(self):
        return self.role == self.ROLE_SHOP_MANAGER


class FoodItems(models.Model):
    """Food items for Cassa Bella Cuisine"""
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='food_items', null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.TextField()
    status = models.BooleanField(default=False)
    extras = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        shop_name = self.shop.name if self.shop else "No Shop"
        return f"{self.name} ({shop_name})"


class ElectronicsItems(models.Model):
    """Electronics items for Best Tech Point-Ashesi"""
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='electronics_items', null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        shop_name = self.shop.name if self.shop else "No Shop"
        return f"{self.name} ({shop_name})"


class GroceryItems(models.Model):
    """Grocery items for Giyark Mini Mart"""
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='grocery_items', null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    image = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        shop_name = self.shop.name if self.shop else "No Shop"
        return f"{self.name} ({shop_name})"

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
    shop        = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
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
    """Order items can be from FoodItems, ElectronicsItems, or GroceryItems"""
    order           = models.ForeignKey(
                         Order,
                         on_delete=models.CASCADE,
                         related_name='items'
                      )
    food_item       = models.ForeignKey('FoodItems', on_delete=models.CASCADE, null=True, blank=True)
    electronics_item = models.ForeignKey('ElectronicsItems', on_delete=models.CASCADE, null=True, blank=True)
    grocery_item    = models.ForeignKey('GroceryItems', on_delete=models.CASCADE, null=True, blank=True)
    quantity        = models.PositiveIntegerField(default=1)
    price           = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # auto-compute line price if not explicitly set
        if not self.price:
            if self.food_item:
                self.price = self.food_item.price * self.quantity
            elif self.electronics_item:
                self.price = self.electronics_item.price * self.quantity
            elif self.grocery_item:
                self.price = self.grocery_item.price * self.quantity
        super().save(*args, **kwargs)

    @property
    def item_name(self):
        """Get the name of the item regardless of type"""
        if self.food_item:
            return self.food_item.name
        elif self.electronics_item:
            return self.electronics_item.name
        elif self.grocery_item:
            return self.grocery_item.name
        return "Unknown Item"

    @property
    def item(self):
        """Get the actual item object regardless of type"""
        if self.food_item:
            return self.food_item
        elif self.electronics_item:
            return self.electronics_item
        elif self.grocery_item:
            return self.grocery_item
        return None

    def __str__(self):
        return f"{self.quantity}× {self.item_name} (Order {self.order.id})"


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
