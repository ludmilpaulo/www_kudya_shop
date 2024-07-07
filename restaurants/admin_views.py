from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Restaurant
from .serializers import RestaurantSerializer
from .utils import send_notification 
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        restaurant = self.get_object()
        restaurant.activate()
        # Send activation email
        mail_subject = "Parabéns! Seu restaurante foi aprovado."
        message = f"""
        <html>
        <body>
            <p>Olá, {restaurant.user.username}!</p>
            <p>Estamos felizes em informar que o seu restaurante <strong>{restaurant.name}</strong> foi aprovado para utilizar a nossa plataforma.</p>
            <p>Agora você pode começar a publicar seus cardápios, receber pedidos e alcançar mais clientes através do nosso marketplace.</p>
            <p>Se precisar de ajuda para configurar seu restaurante na plataforma, não hesite em nos contatar.</p>
            <p>Bem-vindo(a) e sucesso nos negócios!</p>
            <p>&copy; 2024 Sua Empresa. Todos os direitos reservados.</p>
        </body>
        </html>
        """
        send_notification(mail_subject, message, restaurant.user.email)
        return Response({'status': 'restaurant activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        restaurant = self.get_object()
        restaurant.deactivate()
        # Send deactivation email
        mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
        message = f"""
        <html>
        <body>
            <p>Olá, {restaurant.user.username}!</p>
            <p>Lamentamos informar que o seu restaurante <strong>{restaurant.name}</strong> não está qualificado para publicar seu cardápio de comida em nosso mercado.</p>
            <p>Se precisar de mais informações, não hesite em nos contatar.</p>
            <p>&copy; 2024 Sua Empresa. Todos os direitos reservados.</p>
        </body>
        </html>
        """
        send_notification(mail_subject, message, restaurant.user.email)
        return Response({'status': 'restaurant deactivated'})


from django.http import JsonResponse
from .models import Meal

def meal_list(request):
    meals = Meal.objects.select_related('restaurant').all()
    meal_data = []

    for meal in meals:
        meal_data.append({
            'name': meal.name,
            'short_description': meal.short_description,
            'image': meal.image.url,
            'original_price': float(meal.price),
            'price_with_markup': float(meal.price_with_markup),
            'restaurant_name': meal.restaurant.name,
        })

    return JsonResponse({'meals': meal_data})

