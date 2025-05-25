# restaurants/views.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from decimal import Decimal, InvalidOperation
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from .models import Product, Wishlist, Review, ProductCategory

from .serializers import WishlistSerializer, ReviewSerializer, ProductCategorySerializer
from django.shortcuts import get_object_or_404

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Wishlist.objects.filter(user=user)

    @action(detail=False, methods=["delete"], url_path="(?P<user_id>[^/.]+)/(?P<product_id>[^/.]+)")
    def remove(self, request, user_id=None, product_id=None):
        instance = get_object_or_404(Wishlist, user__id=user_id, product__id=product_id)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.request.query_params.get("product")
        if product_id:
            return Review.objects.filter(product_id=product_id)
        return super().get_queryset()

@api_view(["GET"])
def related_products(request, pk):
    # Simple: same category, not same product
    product = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(category=product.category).exclude(pk=pk)[:10]
    data = [
        {
            "id": p.id,
            "name": p.name,
            "images": [{"image": i.image.url} for i in p.images.all()],
            "price": p.price,
            "discount_percentage": p.discount_percentage,
            "on_sale": p.on_sale,
        }
        for p in related
    ]
    return Response(data)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'])
    def by_store(self, request):
        store_id = request.query_params.get('store')
        if not store_id:
            return Response({"error": "Store ID is required."}, status=400)
        products = Product.objects.filter(store_id=store_id)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    

class ProductsByCategoryView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category_id = self.kwargs["category_id"]
        queryset = Product.objects.filter(category_id=category_id)

        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        search = self.request.query_params.get("search")
        on_sale = self.request.query_params.get("on_sale")

        # Defensive filter for min_price
        if min_price:
            try:
                min_price_decimal = Decimal(min_price)
                queryset = queryset.filter(price__gte=min_price_decimal)
            except (InvalidOperation, ValueError):
                pass  # Ignore invalid input

        # Defensive filter for max_price
        if max_price:
            try:
                max_price_decimal = Decimal(max_price)
                queryset = queryset.filter(price__lte=max_price_decimal)
            except (InvalidOperation, ValueError):
                pass

        # Filter by sale
        if on_sale == "true":
            queryset = queryset.filter(on_sale=True)

        # Search (case-insensitive in name)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset
    
    
class CategoryListView(generics.ListAPIView):
    queryset = ProductCategory.objects.all().order_by('name')
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]