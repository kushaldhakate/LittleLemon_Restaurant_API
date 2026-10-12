from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Category, MenuItem, Cart, CartItem, Order, OrderItem

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "title"]

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_title = serializers.CharField(source="category.title", read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_title"]

class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class CartItemSerializer(serializers.ModelSerializer):
    menuitem_title = serializers.CharField(source="menuitem.title", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "menuitem", "menuitem_title", "quantity", "unit_price", "subtotal"]
        read_only_fields = ["unit_price"]

    def get_subtotal(self, obj):
        return obj.quantity * obj.unit_price

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total"]

    def get_total(self, obj):
        return sum((item.quantity * item.unit_price for item in obj.items.all()), start=0)

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem_title = serializers.CharField(source="menuitem.title", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "menuitem_title", "quantity", "unit_price", "subtotal"]

    def get_subtotal(self, obj):
        return obj.quantity * obj.unit_price

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSummarySerializer(read_only=True)
    delivery_crew = UserSummarySerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "total", "date", "items"]
