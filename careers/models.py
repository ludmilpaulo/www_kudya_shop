from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

class Career(models.Model):
    title = models.CharField(max_length=100)
    description = CKEditor5Field('Text', config_name='extends')

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')

    def __str__(self):
        return f"Application for {self.career.title} by {self.full_name}"


# Create your models here.