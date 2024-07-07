from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import admin
from django.template.loader import render_to_string

from restaurants.models.meal import Meal
from .models import RestaurantCategory, Restaurant, OpeningHour

def send_notification(mail_subject, message, to_email):
    from_email = settings.DEFAULT_FROM_EMAIL
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()

@admin.register(RestaurantCategory)
class RestaurantCategoryAdmin(admin.ModelAdmin):
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
                    message = render_to_string('email_templates/approval_email.html', context)
                else:
                    mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
                    message = render_to_string('email_templates/rejection_email.html', context)

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
