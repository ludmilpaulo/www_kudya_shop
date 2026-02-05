from decimal import Decimal
from django.db.models import Q
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Property, PropertyImage
from .serializers import PropertySerializer, PropertyCreateSerializer


class PropertySearchView(generics.ListAPIView):
    """Search properties with filters: type (rent_daily/rent_monthly/buy), city, price range"""
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Property.objects.filter(is_available=True, is_approved=True)

        listing_type = self.request.query_params.get('listing_type')
        if listing_type:
            qs = qs.filter(listing_type=listing_type)

        property_type = self.request.query_params.get('property_type')
        if property_type:
            qs = qs.filter(property_type=property_type)

        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(city__icontains=city)

        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                qs = qs.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass

        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                qs = qs.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass

        bedrooms = self.request.query_params.get('bedrooms')
        if bedrooms:
            try:
                qs = qs.filter(bedrooms__gte=int(bedrooms))
            except (ValueError, TypeError):
                pass

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(city__icontains=search)
            )

        return qs.order_by('-created_at')


class PropertyDetailView(generics.RetrieveAPIView):
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    queryset = Property.objects.filter(is_available=True, is_approved=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_property(request):
    """Create a new property listing (requires auth)"""
    data = request.data.copy()
    if isinstance(data.get('amenities'), str):
        import json
        try:
            data['amenities'] = json.loads(data['amenities']) if data['amenities'] else []
        except (json.JSONDecodeError, TypeError):
            data['amenities'] = []
    serializer = PropertyCreateSerializer(data=data)
    if serializer.is_valid():
        prop = serializer.save(owner=request.user)
        images = request.FILES.getlist('images')
        for i, img in enumerate(images):
            PropertyImage.objects.create(property=prop, image=img, order=i)
        return Response(PropertySerializer(prop).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def property_listing_types(request):
    """Get available listing type options"""
    return Response([
        {'value': 'rent_daily', 'label': 'Rent per Day'},
        {'value': 'rent_monthly', 'label': 'Rent per Month'},
        {'value': 'buy', 'label': 'For Sale'},
    ])


@api_view(['GET'])
@permission_classes([AllowAny])
def property_types(request):
    """Get available property type options"""
    return Response([
        {'value': t[0], 'label': t[1]} for t in Property.PROPERTY_TYPE_CHOICES
    ])
