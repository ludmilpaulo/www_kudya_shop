from django.urls import path, include
from rest_framework.routers import DefaultRouter

from stores.admin_views import StoreViewSet, product_list
from stores.whish_views import WishlistCountView, WishlistDeleteView, WishlistListCreateView
from .product_views import CategoryListView, ProductViewSet, ProductsByCategoryView, ReviewViewSet, WishlistViewSet, related_products
from .store_views import StoreTypeViewSet, StoreViewSet
from stores.store_sign import fornecedor_sign_up
from stores.views import (
    ProductCategoryList,
    OrderListView,
    ProdutoListView,
    StoreCategoryList,
    delete_product,
    fornecedor_add_product,
    get_fornecedor,
    opening_hour_list,
    store_detail,
    store_get_products,
    store_order,
    sse,
    update_location,
    update_product,
)

router = DefaultRouter()
router.register(r"stores", StoreViewSet, basename="store")
#router.register(r"stores", StoreViewSet, basename="store")
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
    path("get_products/", store_get_products, name="fornecedor-get-product"),
    path("delete-product/<int:pk>/", delete_product, name="fornecedor-delete-product"),
    path("store/status/", store_order, name="store_order_api"),
    path("sse/", sse, name="sse"),
    path("update-location/", update_location, name="update-location"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("store/orders/", OrderListView.as_view()),
    path(
        "store-categories/",
        StoreCategoryList.as_view(),
        name="store-category-list",
    ),
    path("restaurant-categories/", StoreCategoryList.as_view(), name="restaurant-category-list"),
    path("meal-categories/", ProductCategoryList.as_view(), name="meal-category-list"),
    path("stores/<int:user_id>/", store_detail, name="store-detail"),
    path(
        "stores/<int:store_pk>/opening_hours/",
        opening_hour_list,
        name="opening-hour-list",
    ),
    path("product-categories/", ProductCategoryList.as_view(), name="product-category-list"),
    path("", include(router.urls)),
    path("api/products/", product_list, name="product-list"),
    
    path('product/categories/', CategoryListView.as_view(), name='category-list'),
    path('products/related/<int:pk>/', related_products, name='related-products'),
    path("product/category/<int:category_id>/products/", ProductsByCategoryView.as_view()),
    path('wishlist/', WishlistListCreateView.as_view(), name='wishlist-list-create'),
    path('wishlist/count/', WishlistCountView.as_view(), name='wishlist-count'),
    path('wishlist/', WishlistDeleteView.as_view(), name='wishlist-delete'),

]
