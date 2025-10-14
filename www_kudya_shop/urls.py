from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from . import views
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("contas.urls")),
    path("customer/", include("customers.urls")),
    path("driver/", include("drivers.urls")),
    path("info/", include("info.urls")),
    path("order/", include("order.urls")),
    path("careers/", include("careers.urls")),
    path("report/", include("report.urls")),
    path("store/", include("stores.urls")),
    path("restaurant/", include("stores.urls")),  # Alias for store endpoints to support legacy frontend apps
    path("manager/", include("management.urls")),
    path("services/", include("services.urls")),  # New services API
    path("api/backup/", views.backup_database, name="backup_database"),
    path("api/delete/", views.delete_database, name="delete_database"),
    path("api/load/", views.load_database, name="load_database"),
    path(
        "ckeditor5/", include("django_ckeditor_5.urls"), name="ck_editor_5_upload_file"
    ),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
