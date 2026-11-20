from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom user model."""

    model = CustomUser
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'role', 'dupr_rating', 'city', 'is_staff', 'is_active',
    ]
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'city']

    fieldsets = UserAdmin.fieldsets + (
        ('PickleScout Info', {
            'fields': ('role', 'contact_number', 'dupr_rating', 'city', 'profile_photo'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('PickleScout Info', {
            'fields': ('role', 'email', 'first_name', 'last_name'),
        }),
    )
