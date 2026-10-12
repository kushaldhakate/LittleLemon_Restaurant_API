from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Category, MenuItem, Cart, CartItem, Order, OrderItem
from .serializers import (CategorySerializer, MenuItemSerializer, CartSerializer,
                          OrderSerializer, UserSummarySerializer)
from .permissions import IsManager, IsDeliveryCrew, in_group

User = get_user_model()

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all().order_by("title")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all().order_by("id")
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["category", "featured"]
    search_fields = ["title", "category__title"]
    ordering_fields = ["price", "title"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsManager()]
        return [permissions.AllowAny()]

class ManagerUsers(APIView):
    permission_classes = [IsManager]
    def get(self, request):
        group = Group.objects.get_or_create(name="Manager")[0]
        return Response(UserSummarySerializer(group.user_set.all(), many=True).data)
    def post(self, request):
        username = request.data.get("username")
        if not username:
            raise ValidationError({"username": "This field is required."})
        user = get_object_or_404(User, username=username)
        group = Group.objects.get_or_create(name="Manager")[0]
        group.user_set.add(user)
        return Response({"message": "user added to the manager group"}, status=200)
    def delete(self, request):
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        group = Group.objects.get_or_create(name="Manager")[0]
        group.user_set.remove(user)
        return Response(status=204)

class DeliveryCrewUsers(APIView):
    permission_classes = [IsManager]
    def get(self, request):
        group = Group.objects.get_or_create(name="Delivery crew")[0]
        return Response(UserSummarySerializer(group.user_set.all(), many=True).data)
    def post(self, request):
        username = request.data.get("username")
        if not username:
            raise ValidationError({"username": "This field is required."})
        user = get_object_or_404(User, username=username)
        group = Group.objects.get_or_create(name="Delivery crew")[0]
        group.user_set.add(user)
        return Response({"message": "user added to the delivery crew"}, status=200)
    def delete(self, request):
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        group = Group.objects.get_or_create(name="Delivery crew")[0]
        group.user_set.remove(user)
        return Response(status=204)

class ItemOfTheDay(APIView):
    permission_classes = [IsManager]
    def get(self, request):
        return Response(MenuItemSerializer(MenuItem.objects.filter(featured=True).first()).data
                        if MenuItem.objects.filter(featured=True).exists() else {})
    def patch(self, request):
        item_id = request.data.get("item_id")
        item = get_object_or_404(MenuItem, pk=item_id)
        item.featured = True
        item.save()
        MenuItem.objects.exclude(pk=item.pk).update(featured=False)
        return Response(MenuItemSerializer(item).data)

class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)
    def post(self, request):
        menuitem = get_object_or_404(MenuItem, pk=request.data.get("menuitem"))
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1:
            raise ValidationError({"quantity": "Must be at least 1."})
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart, menuitem=menuitem,
            defaults={"quantity": quantity, "unit_price": menuitem.price}
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        if request.user.is_staff or in_group(request.user, "Manager"):
            orders = Order.objects.all().prefetch_related("items")
        elif in_group(request.user, "Delivery crew"):
            orders = Order.objects.filter(delivery_crew=request.user).prefetch_related("items")
        else:
            orders = Order.objects.filter(user=request.user).prefetch_related("items")
        return Response(OrderSerializer(orders.order_by("-date"), many=True).data)

    @transaction.atomic
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = list(cart.items.select_related("menuitem"))
        if not cart_items:
            raise ValidationError({"cart": "Your cart is empty."})
        total = sum((i.quantity * i.unit_price for i in cart_items), Decimal("0.00"))
        order = Order.objects.create(user=request.user, total=total)
        for item in cart_items:
            OrderItem.objects.create(order=order, menuitem=item.menuitem,
                                     quantity=item.quantity, unit_price=item.unit_price)
        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if in_group(request.user, "Delivery crew"):
            if order.delivery_crew_id != request.user.id:
                raise PermissionDenied("You can only update orders assigned to you.")
            if "status" in request.data:
                order.status = request.data["status"]
                if order.status not in dict(Order.STATUS_CHOICES):
                    raise ValidationError({"status": "Use pending or delivered."})
                order.save(update_fields=["status"])
            return Response(OrderSerializer(order).data)
        if request.user.is_staff or in_group(request.user, "Manager"):
            if "delivery_crew" in request.data:
                order.delivery_crew = get_object_or_404(User, pk=request.data["delivery_crew"])
            if "status" in request.data:
                order.status = request.data["status"]
            order.save()
            return Response(OrderSerializer(order).data)
        raise PermissionDenied("Not allowed to update this order.")
    def delete(self, request, pk):
        if not (request.user.is_staff or in_group(request.user, "Manager")):
            raise PermissionDenied("Only managers can delete orders.")
        get_object_or_404(Order, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
