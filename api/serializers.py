from django.contrib.auth.models import User
import re
from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from api.models import FoodItems, UserProfile, Shop, ElectronicsItems, GroceryItems
from .models import Order, OrderItem, Payment


class UserSerializer(serializers.ModelSerializer):
    # extra write-only fields
    phone_number           = serializers.CharField(write_only=True, required=True)
    hostel_or_office_name  = serializers.CharField(write_only=True, required=True)
    room_or_office_number  = serializers.CharField(write_only=True, required=True)
    confirm_password       = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = [
            'id', 'first_name', 'last_name',
            'username', 'email', 'password',
            'phone_number',
            'hostel_or_office_name',
            'room_or_office_number',
            'confirm_password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_password(self, value):
        # Require at least 8 chars with uppercase, lowercase, number, and symbol
        regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
        if not regex.match(value):
            raise serializers.ValidationError(
                "Password must be at least 8 characters and include uppercase, lowercase, number, and symbol."
            )
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # pull out profile fields
        phone   = validated_data.pop('phone_number')
        hostel  = validated_data.pop('hostel_or_office_name')
        room    = validated_data.pop('room_or_office_number')
        validated_data.pop('confirm_password')

        # create the User
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()

        # user = User.objects.create_user(**validated_data)

        # create the UserProfile in one go
        UserProfile.objects.create(
            user                  = user,
            phone_number          = phone,
            hostel_or_office_name = hostel,
            room_or_office_number = room,
            role                  = UserProfile.ROLE_STUDENT,
        )

        return user



class UserProfileSerializer(serializers.ModelSerializer):
    # we expose username, but don't require it in input
    username               = serializers.CharField(source='user.username', read_only=True)
    first_name             = serializers.CharField(source='user.first_name', required=False)
    last_name              = serializers.CharField(source='user.last_name',  required=False)
    email                  = serializers.EmailField(source='user.email',    required=False)
    phone_number           = serializers.CharField(required=False)
    hostel_or_office_name  = serializers.CharField(required=False)
    room_or_office_number  = serializers.CharField(required=False)
    role                   = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    shop_id                = serializers.PrimaryKeyRelatedField(
                                 queryset=Shop.objects.all(),
                                 source='shop',
                                 allow_null=True,
                                 required=False
                              )

    class Meta:
        model  = UserProfile
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'hostel_or_office_name',
            'room_or_office_number',
            'role',
            'shop_id',
        ]

    def update(self, instance, validated_data):
        # 1) update nested User
        user_data = validated_data.pop('user', {})
        user      = instance.user
        for attr, val in user_data.items():
            setattr(user, attr, val)
        user.save()

        # 2) update profile fields
        role = validated_data.pop('role', None)
        shop = validated_data.pop('shop', None)  # Pop shop instance if present
        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        request = self.context.get('request')
        
        # Handle role update
        if role is not None:
            can_assign = (
                request
                and getattr(request.user, 'userprofile', None)
                and request.user.userprofile.is_super_admin
            )
            if not can_assign:
                raise serializers.ValidationError({"role": "You do not have permission to change roles."})
            instance.role = role

        # Handle shop assignment (only super admin can assign shops)
        if shop is not None:
            can_assign_shop = (
                request
                and getattr(request.user, 'userprofile', None)
                and request.user.userprofile.is_super_admin
            )
            if not can_assign_shop:
                raise serializers.ValidationError({"shop_id": "You do not have permission to assign shops."})
            instance.shop = shop
        elif 'shop' in validated_data and shop is None:  # If shop_id was explicitly set to null
            can_assign_shop = (
                request
                and getattr(request.user, 'userprofile', None)
                and request.user.userprofile.is_super_admin
            )
            if not can_assign_shop:
                raise serializers.ValidationError({"shop_id": "You do not have permission to assign shops."})
            instance.shop = None

        instance.save()

        return instance

class PasswordResetSerializer(serializers.Serializer):
    email            = serializers.EmailField()
    new_password     = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    # Require at least 8 chars with uppercase, lowercase, number, and symbol
    password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Account does not exist.")
        return value

    def validate(self, data):
        # If they only supplied email, we’re in “check existence” mode
        if 'new_password' not in data and 'confirm_password' not in data:
            return data

        # Otherwise both fields must be present
        if 'new_password' not in data:
            raise serializers.ValidationError({"new_password": "This field is required."})
        if 'confirm_password' not in data:
            raise serializers.ValidationError({"confirm_password": "This field is required."})

        # Strength check
        pwd = data['new_password']
        if not self.password_regex.match(pwd):
            raise serializers.ValidationError({
                "new_password": "Password must be at least 8 characters and include uppercase, lowercase, number, and symbol."
            })

        # Match check
        if pwd != data['confirm_password']:
            raise serializers.ValidationError({"detail": "Passwords do not match."})

        return data

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user



class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'image', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ShopListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing shops"""
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description', 'image', 'is_active']


class FoodSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.filter(is_active=True),
        source='shop',
        write_only=True,
        required=False
    )

    class Meta:
        model = FoodItems
        fields = ['id', 'shop', 'shop_id', 'name', 'price', 'image', 'status', 'extras', 'created_at']
        read_only_fields = ['created_at']


class ElectronicsSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.filter(is_active=True),
        source='shop',
        write_only=True,
        required=False
    )

    class Meta:
        model = ElectronicsItems
        fields = ['id', 'shop', 'shop_id', 'name', 'price', 'image', 'status', 'created_at']
        read_only_fields = ['created_at']


class GrocerySerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(
        queryset=Shop.objects.filter(is_active=True),
        source='shop',
        write_only=True,
        required=False
    )

    class Meta:
        model = GroceryItems
        fields = ['id', 'shop', 'shop_id', 'name', 'price', 'image', 'status', 'created_at']
        read_only_fields = ['created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    # For writing - accept any of the three item types
    food_item = serializers.PrimaryKeyRelatedField(
        queryset=FoodItems.objects.all(), 
        required=False, 
        allow_null=True
    )
    electronics_item = serializers.PrimaryKeyRelatedField(
        queryset=ElectronicsItems.objects.all(), 
        required=False, 
        allow_null=True
    )
    grocery_item = serializers.PrimaryKeyRelatedField(
        queryset=GroceryItems.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    # For reading - return the appropriate item detail
    food_item_detail = FoodSerializer(source='food_item', read_only=True)
    electronics_item_detail = ElectronicsSerializer(source='electronics_item', read_only=True)
    grocery_item_detail = GrocerySerializer(source='grocery_item', read_only=True)
    
    # Helper field to get item name
    item_name = serializers.SerializerMethodField()
    
    def get_item_name(self, obj):
        """Get the item name from the model property"""
        return obj.item_name

    class Meta:
        model  = OrderItem
        fields = [
            'food_item', 'electronics_item', 'grocery_item',
            'quantity', 'price',
            'food_item_detail', 'electronics_item_detail', 'grocery_item_detail',
            'item_name'
        ]
        read_only_fields = ['price', 'food_item_detail', 'electronics_item_detail', 'grocery_item_detail', 'item_name']

    def validate(self, data):
        """Ensure exactly one item type is provided"""
        item_count = sum([
            1 for key in ['food_item', 'electronics_item', 'grocery_item']
            if data.get(key) is not None
        ])
        
        if item_count != 1:
            raise serializers.ValidationError(
                "Exactly one of food_item, electronics_item, or grocery_item must be provided."
            )
        return data


class OrderSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(source='items', many=True, read_only=True)
    customer    = serializers.SerializerMethodField()
    shop        = ShopListSerializer(read_only=True)  # Include shop information

    class Meta:
        model  = Order
        fields = [
            'id',
            'created_at',
            'total_price',
            'status',
            'customer',
            'shop',        # Shop information
            'items',       # for POST
            'order_items', # for GET
        ]
        read_only_fields = ['id', 'created_at', 'total_price', 'order_items', 'status', 'customer', 'shop']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user       = self.context['request'].user

        if not items_data:
            raise serializers.ValidationError({"items": "Order must contain at least one item."})

        # Determine shop from first item (all items should be from same shop)
        first_item_data = items_data[0]
        shop = None
        
        if first_item_data.get('food_item'):
            shop = first_item_data['food_item'].shop
        elif first_item_data.get('electronics_item'):
            shop = first_item_data['electronics_item'].shop
        elif first_item_data.get('grocery_item'):
            shop = first_item_data['grocery_item'].shop
        
        if not shop:
            raise serializers.ValidationError({"items": "Items must be assigned to a shop."})

        # Validate all items are from the same shop
        for item_data in items_data:
            item_shop = None
            if item_data.get('food_item'):
                item_shop = item_data['food_item'].shop
            elif item_data.get('electronics_item'):
                item_shop = item_data['electronics_item'].shop
            elif item_data.get('grocery_item'):
                item_shop = item_data['grocery_item'].shop
            
            if item_shop != shop:
                raise serializers.ValidationError({"items": "All items must be from the same shop."})

        # 1) Create the order header
        order = Order.objects.create(user=user, shop=shop)

        # 2) Populate the line items & tally total
        total = Decimal('0.00')
        for item_data in items_data:
            qty = item_data['quantity']
            line_price = Decimal('0.00')
            
            # Determine which item type and calculate price
            if item_data.get('food_item'):
                item = item_data['food_item']
                item_price = Decimal(str(item.price))
                line_price = (item_price * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                OrderItem.objects.create(
                    order=order,
                    food_item=item,
                    quantity=qty,
                    price=line_price
                )
            elif item_data.get('electronics_item'):
                item = item_data['electronics_item']
                item_price = Decimal(str(item.price))
                line_price = (item_price * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                OrderItem.objects.create(
                    order=order,
                    electronics_item=item,
                    quantity=qty,
                    price=line_price
                )
            elif item_data.get('grocery_item'):
                item = item_data['grocery_item']
                item_price = Decimal(str(item.price))
                line_price = (item_price * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                OrderItem.objects.create(
                    order=order,
                    grocery_item=item,
                    quantity=qty,
                    price=line_price
                )
            
            total += line_price

        # 3) Add delivery fee
        if total > Decimal('150.00'):
            delivery_fee = Decimal('0.00')
        else:
            delivery_fee = Decimal('5.00')
        total += delivery_fee

        # 4) Save the total and return
        order.total_price = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        order.save(update_fields=['total_price'])
        return order

    def get_customer(self, obj):
        request = self.context.get('request')
        try:
            profile = obj.user.userprofile
            role = profile.role
        except UserProfile.DoesNotExist:
            profile = None
            role = None

        if request and hasattr(request, 'user'):
            if obj.user == request.user:
                return {
                    "id": obj.user.id,
                    "username": obj.user.username,
                    "first_name": obj.user.first_name,
                    "last_name": obj.user.last_name,
                    "role": role,
                }

            requester_profile = getattr(request.user, 'userprofile', None)
            if requester_profile and requester_profile.is_staff_role:
                return {
                    "id": obj.user.id,
                    "username": obj.user.username,
                    "first_name": obj.user.first_name,
                    "last_name": obj.user.last_name,
                    "role": role,
                }
        return None


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']


class OrderStatusSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for polling the order's current status.
    """
    class Meta:
        model  = Order
        fields = ['id', 'status']


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=["card", "momo"])
    email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=data['order_id'], user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found or does not belong to user.")
        if order.total_price != data['amount']:
            raise serializers.ValidationError(f"Amount does not match order total. {order.total_price} {data['amount']}")
        data['order'] = order
        return data