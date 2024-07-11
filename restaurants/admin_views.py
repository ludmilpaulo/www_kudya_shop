from venv import logger
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse

from .models import Restaurant, Meal
from .serializers import RestaurantSerializer
from .utils import send_notification
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail

from .models import Restaurant
from .serializers import RestaurantSerializer
from .utils import send_notification


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        restaurant = self.get_object()
        restaurant.activate()
        self._send_activation_email(restaurant)
        return Response({"status": "restaurant activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        restaurant = self.get_object()
        restaurant.deactivate()
        self._send_deactivation_email(restaurant)
        return Response({"status": "restaurant deactivated"})

    def _send_activation_email(self, restaurant):
        context = {
            "user": restaurant.user,
            "restaurant": restaurant,
        }
        mail_subject = "Parabéns! Seu restaurante foi aprovado."
        message = render_to_string("email_templates/approval_email.html", context)
        try:
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [restaurant.user.email],
                html_message=message,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def _send_deactivation_email(self, restaurant):
        context = {
            "user": restaurant.user,
            "restaurant": restaurant,
        }
        mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
        message = render_to_string("email_templates/rejection_email.html", context)
        try:
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [restaurant.user.email],
                html_message=message,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")


from django.http import JsonResponse
from .models import Meal


def meal_list(request):
    meals = Meal.objects.select_related("restaurant").all()
    meal_data = []

    for meal in meals:
        meal_data.append(
            {
                "name": meal.name,
                "short_description": meal.short_description,
                "image": meal.image.url,
                "original_price": float(meal.price),
                "price_with_markup": float(meal.price_with_markup),
                "restaurant_name": meal.restaurant.name,
            }
        )

    return JsonResponse({"meals": meal_data})
