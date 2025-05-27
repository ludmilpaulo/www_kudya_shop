from venv import logger
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse

from .models import Store, Product
from .serializers import StoreSerializer
from .utils import send_notification
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail

from .models import store
from .serializers import StoreSerializer
from .utils import send_notification


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        store = self.get_object()
        store.activate()
        self._send_activation_email(store)
        return Response({"status": "store activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        store = self.get_object()
        store.deactivate()
        self._send_deactivation_email(store)
        return Response({"status": "store deactivated"})

    def _send_activation_email(self, store):
        context = {
            "user": store.user,
            "store": store,
        }
        mail_subject = "Parabéns! Seu storee foi aprovado."
        message = render_to_string("email_templates/approval_email.html", context)
        try:
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [store.user.email],
                html_message=message,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def _send_deactivation_email(self, store):
        context = {
            "user": store.user,
            "store": store,
        }
        mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
        message = render_to_string("email_templates/rejection_email.html", context)
        try:
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [store.user.email],
                html_message=message,
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")


from django.http import JsonResponse



def product_list(request):
    products = Product.objects.select_related("store").all()
    product_data = []

    for product in products:
        product_data.append(
            {
                "name": product.name,
                "short_description": product.short_description,
                "image": product.image.url,
                "original_price": float(product.price),
                "price_with_markup": float(product.price_with_markup),
                "store_name": product.store.name,
            }
        )

    return JsonResponse({"products": product_data})
