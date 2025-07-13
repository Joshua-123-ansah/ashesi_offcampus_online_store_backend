from django.contrib.auth.models import User
import re
from rest_framework import serializers
from api.models import FoodItems, UserProfile
from .models import Order, OrderItem


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
        regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')
        if not regex.match(value):
            raise serializers.ValidationError(
                "Password must be at least 8 characters and include letters and numbers."
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
            room_or_office_number = room
        )

        return user



class UserProfileSerializer(serializers.ModelSerializer):
    # we expose username, but don’t require it in input
    username               = serializers.CharField(source='user.username', read_only=True)
    first_name             = serializers.CharField(source='user.first_name', required=False)
    last_name              = serializers.CharField(source='user.last_name',  required=False)
    email                  = serializers.EmailField(source='user.email',    required=False)
    phone_number           = serializers.CharField(required=False)
    hostel_or_office_name  = serializers.CharField(required=False)
    room_or_office_number  = serializers.CharField(required=False)

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
        ]

    def update(self, instance, validated_data):
        # 1) update nested User
        user_data = validated_data.pop('user', {})
        user      = instance.user
        for attr, val in user_data.items():
            setattr(user, attr, val)
        user.save()

        # 2) update profile fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        return instance

class PasswordResetSerializer(serializers.Serializer):
    email            = serializers.EmailField()
    new_password     = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    password_regex = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')

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
                "new_password": "Password must be at least 8 characters and include letters and numbers."
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



class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItems
        fields = ['id','name', 'price','image', 'status', 'extras']


class OrderItemSerializer(serializers.ModelSerializer):
    food_item = serializers.PrimaryKeyRelatedField(queryset=FoodItems.objects.all())

    class Meta:
        model  = OrderItem
        fields = ['food_item', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(source='items', many=True, read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id',
            'created_at',
            'total_price',
            'items',       # for POST
            'order_items', # for GET
        ]
        read_only_fields = ['id', 'created_at', 'total_price', 'order_items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user       = self.context['request'].user

        # 1) Create the order header
        order = Order.objects.create(user=user)

        # 2) Populate the line items & tally total
        total = 0
        for item in items_data:
            food = item['food_item']
            qty  = item['quantity']
            line_price = food.price * qty
            OrderItem.objects.create(
                order     = order,
                food_item = food,
                quantity  = qty,
                price     = line_price
            )
            total += line_price

        # 3) Save the total and return
        order.total_price = total
        order.save()
        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for polling the order's current status.
    """
    class Meta:
        model  = Order
        fields = ['id', 'status']