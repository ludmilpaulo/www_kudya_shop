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
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='meals')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)  # 10% markup

    @property
    def price_with_markup(self):
        return self.price * (1 + self.percentage / 100)

    def __str__(self):
        return self.name
