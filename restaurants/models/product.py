from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django_ckeditor_5.fields import CKEditor5Field
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


User = get_user_model()

def resize_image(image_field, size=(800, 800)):
    img = Image.open(image_field)
    img.convert('RGB')  # Convert image to RGB (to ensure JPG compatibility)
    img.thumbnail(size, Image.LANCZOS)

    # Save resized image to memory
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=85)  # adjust quality as needed

    # Return new Django-compatible image
    return ContentFile(img_io.getvalue(), image_field.name)




class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name




class Image(models.Model):
    image = models.ImageField(
        max_length=3000, default=None, blank=True, upload_to="product_images/"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Products Images"
        
    def save(self, *args, **kwargs):
        if self.image:
            self.image = resize_image(self.image, size=(800, 800))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.image.name if self.image else "No Image"



class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    SEASON_CHOICES = [
        ("summer", "Summer"),
        ("winter", "Winter"),
        ("all_seasons", "All Seasons"),
    ]
    GENDER_CHOICES = [
        ("unisex", "Unisex"),
        ("male", "Male"),
        ("female", "Female"),
    ]

    name = models.CharField(max_length=255)
    store = models.ForeignKey("Store", on_delete=models.CASCADE, related_name="store")
    description = CKEditor5Field("Text", config_name="extends")
    images = models.ManyToManyField("Image")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    sizes = models.ManyToManyField(Size, blank=True)
    stock = models.PositiveIntegerField(default=0)
    on_sale = models.BooleanField(default=False)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=1, default=3
    )  # % markup
    bulk_sale = models.BooleanField(default=False)
    discount_percentage = models.PositiveIntegerField(default=0)
    season = models.CharField(
        max_length=20, choices=SEASON_CHOICES, default="all_seasons"
    )
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default="unisex"
    )

    def __str__(self):
        return self.name

    @property
    def price_with_markup(self):
        return self.price * (1 + self.percentage / 100)

    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            if self.stock < 10:
                self.notify_low_stock()
        else:
            raise ValueError("Insufficient stock")

    def notify_low_stock(self):
        send_mail(
            "Low Stock Alert",
            f"The stock for {self.name} is below 10. Please restock soon.",
            "admin@example.com",
            ["admin@example.com"],
            fail_silently=False,
        )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    @property
    def category_name(self):
        return self.category.name if self.category else ""

    @property
    def image_urls(self):
        return [image.image.url for image in self.images.all()]


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    class Meta:
        unique_together = ("user", "product")


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(User, related_name="liked_reviews", blank=True)
    dislikes = models.ManyToManyField(User, related_name="disliked_reviews", blank=True)

    def like_count(self):
        return self.likes.count()

    def dislike_count(self):
        return self.dislikes.count()

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"