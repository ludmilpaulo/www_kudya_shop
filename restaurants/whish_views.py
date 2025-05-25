from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Wishlist
from .serializers import WishlistSerializer

class WishlistListCreateView(APIView):
    def get(self, request):
        user_id = request.GET.get('user_id')
        wishlist = Wishlist.objects.filter(user_id=user_id)
        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WishlistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class WishlistDeleteView(APIView):
    def delete(self, request):
        user_id = request.GET.get('user_id')
        product_id = request.GET.get('product_id')
        Wishlist.objects.filter(user_id=user_id, product_id=product_id).delete()
        return Response(status=204)

class WishlistCountView(APIView):
    def get(self, request):
        user_id = request.GET.get('user_id')
        count = Wishlist.objects.filter(user_id=user_id).count()
        return Response({"count": count})
