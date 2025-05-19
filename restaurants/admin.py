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
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


class OpeningHourInline(admin.TabularInline):
    model = OpeningHour
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "phone", "address", "is_approved", "barnner"]
    list_filter = ["is_approved", "barnner"]
    search_fields = ["name", "user__username", "address"]
    inlines = [OpeningHourInline]

    def save_model(self, request, obj, form, change):
        if change and "is_approved" in form.changed_data:
            orig_obj = self.model.objects.get(pk=obj.pk)
            if orig_obj.is_approved != obj.is_approved:
                context = {
                    "user": obj.user,
                }
                if obj.is_approved:
                    mail_subject = "Parabéns! Seu restaurante foi aprovado."
                    message = render_to_string(
                        "email_templates/approval_email.html", context
                    )
                else:
                    mail_subject = "Nós lamentamos! Você não está qualificado para publicar seu cardápio de comida em nosso mercado."
                    message = render_to_string(
                        "email_templates/rejection_email.html", context
                    )

                send_notification(mail_subject, message, context["user"].email)
        super().save_model(request, obj, form, change)


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "category", "price", "quantity"]
    list_filter = ["category", "restaurant"]
    search_fields = ["name", "restaurant__name"]


@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ["restaurant", "day", "from_hour", "to_hour", "is_closed"]
    list_filter = ["restaurant", "day"]
    search_fields = ["restaurant__name"]


from django.contrib import admin
from .models import (
    StoreType,
    StoreCategory,
    Store,
    ProductCategory,
    Image,
    Size,
    Product,
    Wishlist,
    Review,
)

from django.utils.html import format_html


@admin.register(StoreType)
class StoreTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "icon_preview", "description")
    search_fields = ("name",)

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="50" height="50" />', obj.icon.url)
        return "-"
    icon_preview.short_description = "Icon"


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "image_preview")
    search_fields = ("name", "slug")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return "-"
    image_preview.short_description = "Image"


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "store_type", "category", "is_approved", "banner")
    list_filter = ("is_approved", "banner", "store_type")
    search_fields = ("name", "user__username", "phone", "address")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "created_at")
    readonly_fields = ("image_preview",)
    search_fields = ("image",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ImageInline(admin.TabularInline):
    model = Product.images.through
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "category", "price", "stock", "on_sale", "bulk_sale", "season", "gender")
    list_filter = ("category", "store", "on_sale", "bulk_sale", "season", "gender")
    search_fields = ("name", "store__name", "category__name")
    inlines = [ImageInline]
    filter_horizontal = ("images", "sizes")

    fieldsets = (
        (None, {
            "fields": ("name", "store", "description", "category", "images", "sizes")
        }),
        ("Pricing & Stock", {
            "fields": ("price", "percentage", "discount_percentage", "stock", "on_sale", "bulk_sale")
        }),
        ("Attributes", {
            "fields": ("season", "gender")
        }),
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "added_at")
    search_fields = ("user__username", "product__name")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "created_at", "like_count", "dislike_count")
    search_fields = ("user__username", "product__name", "comment")
    list_filter = ("rating", "created_at")

    def like_count(self, obj):
        return obj.likes.count()

    def dislike_count(self, obj):
        return obj.dislikes.count()
