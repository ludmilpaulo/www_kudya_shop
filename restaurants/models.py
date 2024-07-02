from django.db import models
from datetime import time, date, datetime
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class RestaurantCategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    image = models.ImageField(upload_to='category/', blank=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='usuário', blank=True)
    category = models.ForeignKey(RestaurantCategory, related_name='restaurant', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500, verbose_name='Nome do restaurante')
    phone = models.CharField(max_length=500, verbose_name='Telefone do restaurante')
    address = models.CharField(max_length=500, verbose_name='Endereço do restaurante')
    logo = models.ImageField(upload_to='restaurant_logo/', blank=False, verbose_name='Logotipo do restaurante')
    location = models.CharField(max_length=500, blank=True, verbose_name='localização')
    restaurant_license = models.FileField(upload_to='vendor/license', blank=True, verbose_name='Licenca do restaurante')
    barnner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def is_open(self):
        # Check current day's opening hours.
        today_date = date.today()
        today = today_date.isoweekday()

        current_opening_hours = OpeningHour.objects.filter(restaurant=self, day=today)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        is_open = None
        for i in current_opening_hours:
            if not i.is_closed:
                start = str(datetime.strptime(i.from_hour, "%I:%M %p").time())
                end = str(datetime.strptime(i.to_hour, "%I:%M %p").time())
                if start < current_time < end:
                    is_open = True
                    break
                else:
                    is_open = False
        return is_open

    def save(self, *args, **kwargs):
        if self.pk is not None:
            # Update
            orig = Restaurant.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                context = {
                    'user': self.user,
                    'restaurant': self,
                }
                if self.is_approved:
                    # Send notification email
                    mail_subject = "Parabéns! Seu restaurante foi aprovado."
                    message = f"""
                    <html>
                    <body>
                        <p>Olá, {context['user'].username}!</p>
                        <p>Estamos felizes em informar que o seu restaurante <strong>{context['restaurant'].name}</strong> foi aprovado para utilizar a nossa plataforma.</p>
                        <p>Agora você pode começar a publicar seus cardápios, receber pedidos e alcançar mais clientes através do nosso marketplace.</p>
                        <p>Se precisar de ajuda para configurar seu restaurante na plataforma, não hesite em nos contatar.</p>
                        <p>Bem-vindo(a) e sucesso nos negócios!</p>
                        <p>&copy; 2024 Kudya. Todos os direitos reservados.</p>
                    </body>
                    </html>
                    """
                    send_notification(mail_subject, message, context['user'].email)
                else:
                    # Send notification email
                    mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
                    message = f"""
                    <html>
                    <body>
                        <p>Olá, {context['user'].username}!</p>
                        <p>Lamentamos informar que o seu restaurante <strong>{context['restaurant'].name}</strong> não está qualificado para publicar seu cardápio de comida em nosso mercado.</p>
                        <p>Se precisar de mais informações, não hesite em nos contatar.</p>
                        <p>&copy; 2024 SD Kudya. Todos os direitos reservados.</p>
                    </body>
                    </html>
                    """
                    send_notification(mail_subject, message, context['user'].email)
            else:
                # This means it's a new sign-up
                self.send_signup_email()
        return super(Restaurant, self).save(*args, **kwargs)

    def send_signup_email(self):
        """Send a sign-up confirmation email."""
        subject = 'Bem-vindo ao nossa plataforma!'
        message = 'Obrigado por se inscrever. Estamos revisando sua inscrição e entraremos em contato em breve!'
        email_from = settings.EMAIL_HOST_USER
        send_mail(subject, message, email_from, [self.user.email])
from django.db import models

class MealCategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    image = models.ImageField(upload_to='category/', blank=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Meal(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.TextField()
    image = models.ImageField(upload_to='meal_images/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    category = models.ForeignKey(MealCategory, on_delete=models.CASCADE, related_name='meals')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='meals')
    percentage_markup = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def price_with_markup(self):
        return self.price * (1 + self.percentage_markup / 100)

    def __str__(self):
        return self.name


DAYS = [
    (1, "Segunda-feira"),
    (2, "Terça-feira"),
    (3, "Quarta-feira"),
    (4, "Quinta-feira"),
    (5, "Sexta-feira"),
    (6, "Sábado"),
    (7, "Domingo"),
]


def send_notification(mail_subject, message, to_email):
    from_email = settings.DEFAULT_FROM_EMAIL
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()
    
from datetime import time

HOUR_OF_DAY_24 = [(time(h, m).strftime('%I:%M %p'), time(h, m).strftime('%I:%M %p')) for h in range(24) for m in (0, 30)]

class OpeningHour(models.Model):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    from_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    to_hour = models.CharField(choices=HOUR_OF_DAY_24, max_length=10, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ('day', '-from_hour')
        unique_together = ('restaurant', 'day', 'from_hour', 'to_hour')

    def __str__(self):
        return f"{self.get_day_display()} {self.from_hour} - {self.to_hour}"
