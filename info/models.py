from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
from django.utils import timezone

from django_ckeditor_5.fields import CKEditor5Field

class Image(models.Model):
    image = models.ImageField(max_length=3000, default='', blank=True, upload_to='carousel_images/')

    def __str__(self):
        return self.image.name if self.image else ''


class Carousel(models.Model):
	image = models.ManyToManyField(Image)
	title = models.CharField(max_length=150)
	sub_title = models.CharField(max_length=100)

	def __str__(self):
		return self.title


# Create your models here.

class AboutUs(models.Model):
    title = models.CharField(max_length = 50)
    logo = models.ImageField(upload_to="logo/", blank=True, null=True)
    backgroundImage = models.ImageField(upload_to="Back_logo/", blank=True, null=True)
    backgroundApp = models.ImageField(upload_to="Back_logo/", blank=True, null=True)
    about = CKEditor5Field('Text', config_name='extends')
    born_date = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    # Social Network
    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)


    class Meta:
        verbose_name = 'about us '
        verbose_name_plural = 'about us '

    def __str__(self):
        return self.title


class Why_Choose_Us(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()

    class Meta:
        verbose_name = 'why choose us '
        verbose_name_plural = 'why choose us '

    def __str__(self):
        return self.title


class Team(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=50)
    bio = models.CharField(max_length=500)
    image = models.ImageField(upload_to='chef/')
    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = 'Squad'
        verbose_name_plural = 'Squad'

    def __str__(self):
        return self.name




class Contact(models.Model):
    subject = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    message = models.TextField(verbose_name='Conteúdo')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Client contact'
        verbose_name_plural = 'Client contacts'

    def __str__(self):
        return self.subject

class Chat(models.Model):
   # order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

