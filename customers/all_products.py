from rest_framework import generics
from stores.models.product import Product
from stores.serializers import ProductSerializer


class AllProductsList(generics.ListAPIView):
    queryset = Product.objects.all().select_related("category", "store").prefetch_related("images")
    serializer_class = ProductSerializer


