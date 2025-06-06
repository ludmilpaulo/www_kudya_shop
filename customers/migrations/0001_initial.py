# Generated by Django 5.2 on 2025-06-03 00:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, upload_to='customer/')),
                ('phone', models.CharField(blank=True, max_length=500, verbose_name='telefone')),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='Endereço')),
                ('location', models.CharField(blank=True, max_length=500, verbose_name='localização')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL, verbose_name='usuário')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
            },
        ),
    ]
