from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from customers.models import Customer
from .models import Driver

User = get_user_model()

# Unregister the default User admin
admin.site.unregister(User)


class DriverInline(admin.StackedInline):
    model = Driver
    can_delete = False
    verbose_name_plural = "drivers"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    inlines = [DriverInline]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "is_customer",
                    "is_driver",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                    "is_customer",
                    "is_driver",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_customer",
        "is_driver",
    )
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)


admin.site.register(User, UserAdmin)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "address", "location")
    search_fields = ("user__username", "phone", "address", "location")
    list_filter = ("user__is_active", "user__is_staff")
