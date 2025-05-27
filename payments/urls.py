from django.urls import path
from . import views

urlpatterns = [
    path('api/payments/', views.create_payment),
    path('api/payments/<int:pk>/', views.get_payment),
]
