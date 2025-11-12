from django.contrib import admin
from .models import FoodItems, Order, OrderItem, Payment, UserProfile

@admin.register(FoodItems)
class FoodItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price','image', 'status', 'extras')  # adjust to your fields
    search_fields = ('status',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'created_at', 'status', 'total_price')
    list_filter   = ('status', 'created_at')
    search_fields = ('user__username', 'id')
    inlines       = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ('order', 'food_item', 'quantity', 'price')
    search_fields = ('food_item__name',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'amount', 'payment_method', 'status', 'paystack_reference', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'order__id', 'paystack_reference')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'hostel_or_office_name', 'room_or_office_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'hostel_or_office_name')


# —–– or, equivalently —––—
# admin.site.register(FoodItems, FoodItemsAdmin)
