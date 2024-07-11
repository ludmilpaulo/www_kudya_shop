# Generated by Django 5.0.3 on 2024-07-06 12:53

import django.db.models.deletion
import django_ckeditor_5.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Career",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                (
                    "description",
                    django_ckeditor_5.fields.CKEditor5Field(verbose_name="Text"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="JobApplication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("resume", models.FileField(upload_to="resumes/")),
                (
                    "career",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="careers.career"
                    ),
                ),
            ],
        ),
    ]
