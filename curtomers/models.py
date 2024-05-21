from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()





# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='customer', verbose_name='usuário')
    avatar = models.ImageField(upload_to='customer/', blank=True)
    phone = models.CharField(max_length=500, blank=True, verbose_name='telefone')
    address = models.CharField(max_length=500, blank=True, verbose_name='Endereço')

    class Meta:
        verbose_name ='Cliente'
        verbose_name_plural ='Clientes'

    def __str__(self):
        return self.user.get_username()