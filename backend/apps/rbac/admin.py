from django.contrib import admin
from .models import Role, UserRole


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_system")
    search_fields = ("name", "slug")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "assigned_by", "assigned_at")
    search_fields = ("user__username", "role__name")
