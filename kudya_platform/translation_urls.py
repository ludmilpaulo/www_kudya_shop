from django.urls import path
from .views import translations_bundle

urlpatterns = [
    path('', translations_bundle, name='api-translations'),
]
