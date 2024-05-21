from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib import admin
from .models import RestaurantCategory, MealCategory, Restaurant, Meal, OpeningHour

def send_notification(mail_subject, message, to_email):
    from_email = settings.DEFAULT_FROM_EMAIL
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()

@admin.register(RestaurantCategory)
class RestaurantCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(MealCategory)
class MealCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class OpeningHourInline(admin.TabularInline):
    model = OpeningHour
    extra = 1

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'phone', 'address', 'is_approved', 'barnner']
    list_filter = ['is_approved', 'barnner']
    search_fields = ['name', 'user__username', 'address']
    inlines = [OpeningHourInline]

    def save_model(self, request, obj, form, change):
        if change and 'is_approved' in form.changed_data:
            orig_obj = self.model.objects.get(pk=obj.pk)
            if orig_obj.is_approved != obj.is_approved:
                context = {
                    'user': obj.user,
                }
                if obj.is_approved:
                    mail_subject = "Parabéns! Seu restaurante foi aprovado."
                    message = f"""
                    <html>
                    <body>
                        <p>Olá, {context['user'].username}!</p>
                        <p>Estamos felizes em informar que o seu restaurante <strong>{obj.name}</strong> foi aprovado para utilizar a nossa plataforma.</p>
                        <p>Agora você pode começar a publicar seus cardápios, receber pedidos e alcançar mais clientes através do nosso marketplace.</p>
                        <p>Se precisar de ajuda para configurar seu restaurante na plataforma, não hesite em nos contatar.</p>
                        <p>Bem-vindo(a) e sucesso nos negócios!</p>
                        <p>&copy; 2024 Sua Empresa. Todos os direitos reservados.</p>
                    </body>
                    </html>
                    """
                    send_notification(mail_subject, message, context['user'].email)
                else:
                    mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
                    message = f"""
                    <html>
                    <body>
                        <p>Olá, {context['user'].username}!</p>
                        <p>Lamentamos informar que o seu restaurante <strong>{obj.name}</strong> não está qualificado para publicar seu cardápio de comida em nosso mercado.</p>
                        <p>Se precisar de mais informações, não hesite em nos contatar.</p>
                        <p>&copy; 2024 Sua Empresa. Todos os direitos reservados.</p>
                    </body>
                    </html>
                    """
                    send_notification(mail_subject, message, context['user'].email)
        super().save_model(request, obj, form, change)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'quantity']
    list_filter = ['category', 'restaurant']
    search_fields = ['name', 'restaurant__name']

@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'day', 'from_hour', 'to_hour', 'is_closed']
    list_filter = ['restaurant', 'day']
    search_fields = ['restaurant__name']
