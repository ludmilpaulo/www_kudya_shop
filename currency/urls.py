# currency/urls.py
from django.urls import path
from . import views

app_name = 'currency'

urlpatterns = [
    path('rates/', views.get_exchange_rates, name='exchange-rates'),
    path('convert/', views.convert_currency, name='convert-currency'),
    path('update/', views.force_update_rates, name='force-update'),
]

