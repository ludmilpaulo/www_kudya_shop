from django.urls import path, include
from rest_framework.routers import DefaultRouter

from restaurants.admin_views import RestaurantViewSet, meal_list
from restaurants.whish_views import WishlistCountView, WishlistDeleteView, WishlistListCreateView
from .product_views import CategoryListView, ProductViewSet, ProductsByCategoryView, ReviewViewSet, WishlistViewSet, related_products
from .store_views import StoreTypeViewSet, StoreViewSet
from restaurants.restaurant_sign import fornecedor_sign_up
from restaurants.views import (
    MealCategoryList,
    OrderListView,
    ProdutoListView,
    RestaurantCategoryList,
    delete_product,
    fornecedor_add_product,
    get_fornecedor,
    opening_hour_list,
    restaurant_detail,
    restaurant_get_meals,
    restaurant_order,
    sse,
    update_location,
    update_product,
)

router = DefaultRouter()
router.register(r"restaurants", RestaurantViewSet, basename="restaurant")
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"store-types", StoreTypeViewSet, basename="store-type")
router.register(r'products', ProductViewSet, basename='product')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path("fornecedor/", fornecedor_sign_up),
    path("get_fornecedor/", get_fornecedor, name="get_fornecedor"),
    path("get_products/", ProdutoListView.as_view()),
    path("add-product/", fornecedor_add_product, name="fornecedor-add-product"),
    path("update-product/<int:pk>/", update_product, name="update_product"),
    path("get_products/", restaurant_get_meals, name="fornecedor-get-product"),
    path("delete-product/<int:pk>/", delete_product, name="fornecedor-delete-product"),
    path("restaurant/status/", restaurant_order, name="restaurant_order_api"),
    path("sse/", sse, name="sse"),
    path("update-location/", update_location, name="update-location"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("restaurant/orders/", OrderListView.as_view()),
    path(
        "restaurant-categories/",
        RestaurantCategoryList.as_view(),
        name="restaurant-category-list",
    ),
    path("restaurants/<int:user_id>/", restaurant_detail, name="restaurant-detail"),
    path(
        "restaurants/<int:restaurant_pk>/opening_hours/",
        opening_hour_list,
        name="opening-hour-list",
    ),
    path("meal-categories/", MealCategoryList.as_view(), name="meal-category-list"),
    path("", include(router.urls)),
    path("api/meals/", meal_list, name="meal-list"),
    
    path('product/categories/', CategoryListView.as_view(), name='category-list'),
    path('products/related/<int:pk>/', related_products, name='related-products'),
    path("product/category/<int:category_id>/products/", ProductsByCategoryView.as_view()),
    path('wishlist/', WishlistListCreateView.as_view(), name='wishlist-list-create'),
    path('wishlist/count/', WishlistCountView.as_view(), name='wishlist-count'),
    path('wishlist/', WishlistDeleteView.as_view(), name='wishlist-delete'),

]
