from django.contrib import admin
from .models import FoodItems, Order, OrderItem

@admin.register(FoodItems)
class FoodItemsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price','image', 'status')  # adjust to your fields
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

# —–– or, equivalently —––—
# admin.site.register(FoodItems, FoodItemsAdmin)
