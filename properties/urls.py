from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.PropertySearchView.as_view(), name='property-search'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='property-detail'),
    path('create/', views.create_property, name='property-create'),
    path('listing-types/', views.property_listing_types, name='property-listing-types'),
    path('property-types/', views.property_types, name='property-types'),
]
