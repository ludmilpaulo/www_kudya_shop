from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from contas.serializers import DriverSignupSerializer, UserSerializer
from drivers.models import Driver
from drivers.serializers import DriverSerializer
from order.models import Order
from order.serializers import OrderDriverSerializer, OrderSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import *
from rest_framework.authtoken.models import Token


# from django.contrib.auth.models import User
from rest_framework.parsers import *


from django.contrib.auth import get_user_model

User = get_user_model()


AccessToken = Token


class DriverSignupView(generics.GenericAPIView):
    serializer_class = DriverSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": Token.objects.get(user=user).key,
                "user_id": user.pk,
                "message": "Conta criada com sucesso",
                "username": user.username,
                "status": "201",
            }
        )


####################################################
# DRIVERS
####################################################
@api_view(["GET"])
def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status=Order.READY, driver=None).order_by("-id"), many=True
    ).data

    return JsonResponse({"orders": orders})




@api_view(["POST"])
def driver_pick_order(request):
    data = request.data
    print(data)
    access = Token.objects.get(key=data["access_token"]).user
    driver = Driver.objects.get(user=access)

    if Order.objects.filter(driver=driver).exclude(status=Order.DELIVERED):
        return JsonResponse(
            {"status": "failed", "error": "Você só pode pegar outros pedidos depois de entregar o pedido anterior"}
        )

    try:
        order = Order.objects.get(id=data["order_id"], driver=None, status=Order.READY)
        order.driver = driver
        order.status = Order.ONTHEWAY
        order.picked_at = timezone.now()
        order.save()
        return JsonResponse({"status": "success", "message": "Ótimo, por favor, você tem no máximo 20 minutos para concluir esta entrega"})
    except Order.DoesNotExist:
        return JsonResponse({"status": "failed", "error": "Este pedido foi retirado por outro."})



# GET params: access_token
@api_view(["POST"])
def driver_get_latest_order(request):
    # Get token
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile

    driver = Driver.objects.get(user=access)

    order = OrderSerializer(
        Order.objects.filter(driver=driver).order_by("picked_at").last()
    ).data

    return JsonResponse({"order": order})




@api_view(["POST"])
def driver_complete_order(request):
    # Get token
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    try:
        order = Order.objects.get(id=data["order_id"], driver=driver)
    except Order.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Order not found or not assigned to this driver"})

    if order.secret_pin == data["secret_pin"]:
        order.status = Order.DELIVERED
        order.save()
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"status": "error", "message": "Incorrect PIN"})


# POST - params: access_token, "lat,lng"
@api_view(["POST"])
def driver_update_location(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    # Set location string => database
    driver.location = data["location"]
    driver.save()

    return JsonResponse({"status": "Driver location successfully sent"})


# GET params: access_token
@api_view(["POST"])
def driver_get_order_history(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    order_history = OrderSerializer(
        Order.objects.filter(driver=driver, status=Order.DELIVERED).order_by(
            "picked_at"
        ),
        many=True,
        context={"request": request},
    ).data

    return JsonResponse({"order_history": order_history})


@api_view(["POST"])
def driver_get_detais(request):
    data = request.data

    customer_detais = DriverSerializer(Driver.objects.get(user_id=data["user_id"])).data

    return JsonResponse({"customer_detais": customer_detais})


@api_view(["POST"])
@parser_classes([JSONParser, MultiPartParser, FormParser, FileUploadParser])
def driver_update_profile(request, format=None):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user

    driver = Driver.objects.get(user=access)

    # Set location string => database
    driver.avatar = request.FILES.get("avatar")
    # driver.avatar = data['avatar']
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
    access = Token.objects.get(key=data["access_token"]).user

    # Get profile

    driver = Driver.objects.get(user=access)

    order = OrderDriverSerializer(
        Driver.objects.filter(user=driver).order_by("-id")
    ).data

    return JsonResponse({"order": order})


def test_reject_order_view(request, driver_id):
    if request.method == "POST":
        driver = Driver.objects.get(pk=driver_id)
        driver.increment_rejected_orders()
        return JsonResponse(
            {
                "status": "success",
                "message": "Order rejection recorded and email notification sent if limit reached.",
            }
        )
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."})



@csrf_exempt
@api_view(['POST'])
def reject_order(request):
    print("Step 1: Entered reject_order function")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Step 2: Parsed request body", data)
            order_id = data.get('order_id')
            access_token = data.get('access_token')
            print(f"Step 3: Order ID: {order_id}, Access Token: {access_token}")

            # Authenticate the token
            access = Token.objects.get(key=access_token).user
            print("Step 4: Token authenticated, user:", access)

            # Get the driver
            driver = Driver.objects.get(user=access)
            print(f"Step 5: Driver found. Driver ID: {driver.id}")

            # Increment rejected orders count for the driver
            driver.increment_rejected_orders()
            driver.send_rejection_warning_email()
            print("Step 6: Driver rejection count incremented")

            return JsonResponse({"status": "success", "message": "Order rejection recorded."})
        except Driver.DoesNotExist:
            print("Step 7: Driver not found")
            return JsonResponse({"status": "error", "message": "Driver not found."}, status=404)
        except Token.DoesNotExist:
            print("Step 8: Token not found")
            return JsonResponse({"status": "error", "message": "Invalid token."}, status=403)
        except Exception as e:
            print(f"Step 9: An error occurred: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    print("Step 10: Invalid request method")
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)





@api_view(["POST"])
def get_ongoing_order(request):
    data = request.data
    access = Token.objects.get(key=data["access_token"]).user
    driver = Driver.objects.get(user=access)

    try:
        ongoing_order = Order.objects.filter(driver=driver, status=Order.ONTHEWAY).first()
        if ongoing_order:
            order_data = {
                "id": ongoing_order.id,
                "store": {
                    "name": ongoing_order.store.name,
                    "phone": ongoing_order.store.phone,
                    "address": ongoing_order.store.address,
                    "logo": ongoing_order.store.logo.url if ongoing_order.store.logo else None,
                    "location": ongoing_order.store.location,
                },
                "customer": {
                    "avatar": ongoing_order.customer.avatar.url if ongoing_order.customer.avatar else None,
                    "phone": ongoing_order.customer.phone,
                    "name": ongoing_order.customer.user.username,
                    "address": ongoing_order.customer.address,
                    "location": ongoing_order.customer.location,
                },
                "order_details": [
                    {
                        "id": detail.id,
                        "product": {
                            "id": detail.product.id,
                            "name": detail.product.name,
                            "price": str(detail.product.price)
                        },
                        "quantity": detail.quantity,
                        "sub_total": str(detail.sub_total)
                    } for detail in ongoing_order.order_details.all()
                ],
                "status": ongoing_order.status,
                "address": ongoing_order.address,
                "secret_pin":ongoing_order.secret_pin,
            }
            return JsonResponse({"status": "success", "order": order_data})
        else:
            return JsonResponse({"status": "success", "order": None})
    except Driver.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Driver not found."}, status=404)
    except Order.DoesNotExist:
        return JsonResponse({"status": "success", "order": None})



@api_view(["POST"])
def verify_order(request):
    data = request.data
    print(data)
    access = Token.objects.get(key=data["access_token"]).user
    driver = Driver.objects.get(user=access)

    try:
        order = Order.objects.get(id=data["order_id"], driver=driver, status=Order.ONTHEWAY)
        # Verify if all items are checked
        received_items = data.get("received_items", [])
        if len(received_items) != order.order_details.count():
            return JsonResponse({"status": "failed", "message": "All items have not been received."})

        if order.secret_pin == data["pin"]:
            order.status = Order.VERIFIED  # Change to VERIFIED status
            order.save()
            return JsonResponse({"status": "success", "message": "Order verified successfully."})
        else:
            return JsonResponse({"status": "failed", "message": "Invalid PIN."})
    except Order.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Order not found or you are not assigned to this order."})




@api_view(["POST"])
def get_verified_order(request):
    data = request.data
    try:
        access = Token.objects.get(key=data["access_token"]).user
        driver = Driver.objects.get(user=access)
        
        # Fetch the first verified order for the driver
        verified_order = Order.objects.filter(driver=driver, status=Order.VERIFIED).first()
        
        if verified_order:
            order_data = {
                "id": verified_order.id,
                "store": {
                    "name": verified_order.store.name,
                    "phone": verified_order.store.phone,
                    "address": verified_order.store.address,
                    "logo": verified_order.store.logo.url if verified_order.store.logo else None,
                    "location": verified_order.store.location,
                },
                 "customer": {
                    "name": verified_order.customer.user.username,
                    "avatar": verified_order.customer.avatar.url if verified_order.customer.avatar else None,
                    "phone": verified_order.customer.phone,
                    "address": verified_order.customer.address,
                    "location": verified_order.customer.location,
                },
                 "driver": {
                    "name": verified_order.driver.user.username,
                    "avatar": verified_order.driver.avatar.url if verified_order.customer.avatar else None,
                    "phone": verified_order.driver.phone,
                    "address": verified_order.driver.address,
                    "location": verified_order.driver.location,
                },
                "order_details": [
                    {
                        "id": detail.id,
                        "product": {
                            "id": detail.product.id,
                            "name": detail.product.name,
                            "price": detail.product.price
                        },
                        "quantity": detail.quantity,
                        "sub_total": detail.sub_total
                    } for detail in verified_order.order_details.all()
                ],
                "status": verified_order.status,
                "address": verified_order.address,
                "secret_pin": verified_order.secret_pin,
            }
            return JsonResponse({"status": "success", "order": order_data})
        else:
            return JsonResponse({"status": "success", "order": None})
    except Token.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid access token."}, status=401)
    except Driver.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Driver not found."}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
