from django.utils import timezone
from django.http import JsonResponse



from contas.serializers import DriverSignupSerializer, UserSerializer
from drivers.models import Driver
from drivers.serializers import DriverSerializer
from order.models import Order
from order.serializers import OrderDriverSerializer, OrderSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import *
from rest_framework.authtoken.models import Token


#from django.contrib.auth.models import User
from rest_framework.parsers import *


from django.contrib.auth import get_user_model
User = get_user_model()



AccessToken = Token

class DriverSignupView(generics.GenericAPIView):
    serializer_class=DriverSignupSerializer
    def post(self, request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        return Response({
            "user":UserSerializer(user, context=self.get_serializer_context()).data,
            "token":Token.objects.get(user=user).key,
            'user_id':user.pk,
            "message":"Conta criada com sucesso",
            'username':user.username,
            "status":"201"
        })

####################################################
# DRIVERS
####################################################
@api_view(['GET'])
def driver_get_ready_orders(request):
    orders = OrderSerializer(Order.objects.filter(status=Order.READY,
                                                  driver=None).order_by("-id"),
                             many=True).data

    return JsonResponse({"orders": orders})


@api_view(['POST'])
# params: access_token, order_id
def driver_pick_order(request):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

     # Get profile

    driver = Driver.objects.get(user=access)

    # Check if driver can only pick up one order at the same time
    if Order.objects.filter(driver=driver).exclude(status=Order.DELIVERED):
        return JsonResponse({
            "status":"failed",
            "error": "Você só pode pegar outros pedidos depois de entregar o pedido anterior"
        })

    try:
        order = Order.objects.get(id=data["order_id"],
                                  driver=None,
                                  status=Order.READY)
        order.driver = driver
        order.status = Order.ONTHEWAY
        order.picked_at = timezone.now()
        order.save()

        return JsonResponse({"status": "Ótimo, por favor, você tem no máximo 20 minutos para concluir esta entrega"})

    except Order.DoesNotExist:
        return JsonResponse({
            "status":
            "failed",
            "error":
            "Este pedido foi retirado por outro."
        })

    return JsonResponse({})


# GET params: access_token
@api_view(['POST'])
def driver_get_latest_order(request):
    # Get token
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

     # Get profile

    driver = Driver.objects.get(user=access)

    order = OrderSerializer(
        Order.objects.filter(driver=driver).order_by("picked_at").last()).data

    return JsonResponse({"order": order})


# POST params: access_token, order_id
@api_view(['POST'])
def driver_complete_order(request):
    # Get token
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    driver = Driver.objects.get(user=access)

    order = Order.objects.get(id=data["order_id"], driver=driver)
    order.status = Order.DELIVERED
    order.save()

    return JsonResponse({"status": "success"})

@api_view(["POST"])
# GET params: access_token
def driver_get_revenue(request):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    driver = Driver.objects.get(user=access)

    from datetime import timedelta

    revenue = {}
    today = timezone.now()
    current_weekdays = [
        today + timedelta(days=i)
        for i in range(0 - today.weekday(), 7 - today.weekday())
    ]

    for day in current_weekdays:
        orders = Order.objects.filter(driver=driver,
                                      status=Order.DELIVERED,
                                      created_at__year=day.year,
                                      created_at__month=day.month,
                                      created_at__day=day.day)

        revenue[day.strftime("%a")] = sum(order.total for order in orders)

    return JsonResponse({"revenue": revenue})


# POST - params: access_token, "lat,lng"
@api_view(["POST"])
def driver_update_location(request):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    driver = Driver.objects.get(user=access)

    # Set location string => database
    driver.location = data["location"]
    driver.save()

    return JsonResponse({"status": "Driver location successfully sent"})


# GET params: access_token
@api_view(["POST"])
def driver_get_order_history(request):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    driver = Driver.objects.get(user=access)


    order_history = OrderSerializer(Order.objects.filter(
        driver=driver, status=Order.DELIVERED).order_by("picked_at"),
                                    many=True,
                                    context={
                                        "request": request
                                    }).data

    return JsonResponse({"order_history": order_history})


@api_view(['POST'])
def driver_get_detais(request):
    data = request.data

    customer_detais = DriverSerializer(
         Driver.objects.get(user_id=data['user_id'])).data
     

    return JsonResponse({"customer_detais": customer_detais})







@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def driver_update_profile(request, format=None):
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

    driver = Driver.objects.get(user=access)

    # Set location string => database
    driver.avatar = request.FILES.get('avatar')
    #driver.avatar = data['avatar']
    driver.phone = data["phone"]
    driver.address = data["address"]
    driver.save()

    driver_user = User.objects.get(username=access)
    driver_user.first_name = data["first_name"]
    driver_user.last_name = data["last_name"]
    driver_user.save()

    return JsonResponse({"status": "Os Seus Dados enviados com sucesso"})




@api_view(["POST"])
def driver_get_profile(request):
     # Get token
    data = request.data
    access = Token.objects.get(key=data['access_token']).user

     # Get profile

    driver = Driver.objects.get(user=access)

    order = OrderDriverSerializer(
        Driver.objects.filter(user=driver).order_by("-id")).data

    return JsonResponse({"order": order})

