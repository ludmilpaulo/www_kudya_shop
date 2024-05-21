from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()




class Driver(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='driver', verbose_name='Utilizador')
    avatar = models.ImageField(upload_to='driver/', blank=True)
    phone = models.CharField(max_length=500, blank=True, verbose_name='telefone')
    address = models.CharField(max_length=500, blank=True, verbose_name='Endereço')
    location = models.CharField(max_length=500, blank=True, verbose_name='localização')

    class Meta:
        verbose_name ='Motorista'
        verbose_name_plural ='Motoristas'


    def __str__(self):
        return self.user.get_username()