from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (CategoryList, MenuItemViewSet, ManagerUsers, DeliveryCrewUsers,
                    ItemOfTheDay, CartView, OrdersView, OrderDetail)

router = DefaultRouter()
router.register("menu-items", MenuItemViewSet, basename="menu-item")

urlpatterns = [
    path("", include(router.urls)),
    path("categories", CategoryList.as_view(), name="categories"),
    path("groups/manager/users", ManagerUsers.as_view(), name="manager-users"),
    path("groups/delivery-crew/users", DeliveryCrewUsers.as_view(), name="delivery-crew-users"),
    path("featured", ItemOfTheDay.as_view(), name="featured"),
    path("cart/menu-items", CartView.as_view(), name="cart"),
    path("orders", OrdersView.as_view(), name="orders"),
    path("orders/<int:pk>", OrderDetail.as_view(), name="order-detail"),
]
