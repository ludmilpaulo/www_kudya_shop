# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import StoreType
from .serializers import StoreTypeSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from .models import Store, StoreType
from .serializers import StoreSerializer, StoreTypeSerializer


class StoreTypeListView(APIView):
    def get(self, request):
        store_types = StoreType.objects.all()
        serializer = StoreTypeSerializer(store_types, many=True)
        return Response(serializer.data)


class StoreViewSet(ModelViewSet):
    serializer_class = StoreSerializer
    queryset = Store.objects.filter(is_approved=True)
    filter_backends = [SearchFilter]
    search_fields = ['name', 'address']

    def get_queryset(self):
        queryset = super().get_queryset()
        store_type_id = self.request.query_params.get('store_type')
        if store_type_id:
            queryset = queryset.filter(store_type__id=store_type_id)
        return queryset


class StoreTypeViewSet(ModelViewSet):
    serializer_class = StoreTypeSerializer
    queryset = StoreType.objects.all()
    
    
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from .models import Store, StoreType
from .serializers import StoreSerializer, StoreTypeSerializer

class StoreViewSet(ModelViewSet):
    serializer_class = StoreSerializer
    queryset = Store.objects.filter(is_approved=True)
    filter_backends = [SearchFilter]
    search_fields = ['name', 'address']

    def get_queryset(self):
        queryset = super().get_queryset()
        store_type_id = self.request.query_params.get('store_type')
        if store_type_id:
            queryset = queryset.filter(store_type__id=store_type_id)
        return queryset


class StoreTypeViewSet(ModelViewSet):
    serializer_class = StoreTypeSerializer
    queryset = StoreType.objects.all()
