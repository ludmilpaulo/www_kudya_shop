from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contas', '0002_user_city_user_country_user_is_verified_user_phone_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('google', 'Google'), ('facebook', 'Facebook'), ('instagram', 'Instagram'), ('tiktok', 'TikTok')], db_index=True, max_length=20)),
                ('provider_user_id', models.CharField(db_index=True, max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('extra_data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['provider', 'provider_user_id'], name='contas_soci_provide_idx')],
                'unique_together': {('provider', 'provider_user_id')},
            },
        ),
    ]
