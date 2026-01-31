from django.contrib import admin
from .models import (
    Shop,
    FoodItems,
    ElectronicsItems,
    GroceryItems,
    Order,
    OrderItem,
    Payment,
    UserProfile
)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FoodItems)
class FoodItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'status', 'created_at')
    list_filter = ('shop', 'status', 'created_at')
    search_fields = ('name', 'extras', 'shop__name')
    readonly_fields = ('created_at',)


@admin.register(ElectronicsItems)
class ElectronicsItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'status', 'created_at')
    list_filter = ('shop', 'status', 'created_at')
    search_fields = ('name', 'shop__name')
    readonly_fields = ('created_at',)


@admin.register(GroceryItems)
class GroceryItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'price', 'status', 'created_at')
    list_filter = ('shop', 'status', 'created_at')
    search_fields = ('name', 'shop__name')
    readonly_fields = ('created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'shop', 'created_at', 'status', 'total_price')
    list_filter   = ('status', 'shop', 'created_at')
    search_fields = ('user__username', 'id', 'shop__name')
    inlines       = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ('order', 'get_item_name', 'get_item_type', 'quantity', 'price')
    list_filter = ('order__shop',)
    search_fields = ('food_item__name', 'electronics_item__name', 'grocery_item__name', 'order__id')
    
    def get_item_name(self, obj):
        """Display the name of the item regardless of type"""
        return obj.item_name
    get_item_name.short_description = 'Item Name'
    
    def get_item_type(self, obj):
        """Display the type of item"""
        if obj.food_item:
            return 'Food'
        elif obj.electronics_item:
            return 'Electronics'
        elif obj.grocery_item:
            return 'Grocery'
        return 'Unknown'
    get_item_type.short_description = 'Item Type'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'amount', 'payment_method', 'status', 'paystack_reference', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'order__id', 'paystack_reference')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'shop', 'phone_number', 'hostel_or_office_name', 'room_or_office_number')
    list_filter = ('role', 'shop')
    search_fields = ('user__username', 'user__email', 'hostel_or_office_name', 'shop__name')


# —–– or, equivalently —––—
# admin.site.register(FoodItems, FoodItemsAdmin)
