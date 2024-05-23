from django.contrib import admin
from .models import (
    Image,
    Carousel,
    AboutUs,
    Why_Choose_Us,
    Team,
    Contact,
    Chat
)

# Register the Image model
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image')
    search_fields = ('image',)

# Register the Carousel model with a custom admin to display many-to-many relationships
@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sub_title')
    search_fields = ('title', 'sub_title')
    filter_horizontal = ('image',)

# Register the AboutUs model
@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'born_date', 'address', 'phone', 'email')
    search_fields = ('title', 'address', 'phone', 'email')

# Register the Why_Choose_Us model
@admin.register(Why_Choose_Us)
class WhyChooseUsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)

# Register the Team model
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'title', 'bio')
    search_fields = ('name', 'title', 'bio')

# Register the Contact model
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'email', 'phone', 'timestamp')
    search_fields = ('subject', 'email', 'phone')
    list_filter = ('timestamp',)

# Register the Chat model
@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'message', 'timestamp')
    search_fields = ('sender__username', 'message')
    list_filter = ('timestamp',)
