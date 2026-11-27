from django.contrib import admin
from .models import Court, FavoriteCourt, CourtReport, CourtReview


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'city', 'facility_type', 'surface_type',
        'number_of_courts', 'rental_price', 'is_active', 'created_by',
    ]
    list_filter = ['facility_type', 'surface_type', 'city', 'is_active']
    search_fields = ['name', 'city', 'address', 'description']


@admin.register(FavoriteCourt)
class FavoriteCourtAdmin(admin.ModelAdmin):
    list_display = ['user', 'court', 'added_at']
    list_filter = ['added_at']


@admin.register(CourtReport)
class CourtReportAdmin(admin.ModelAdmin):
    list_display = ['court', 'reported_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['court__name', 'reported_by__username', 'reason']


@admin.register(CourtReview)
class CourtReviewAdmin(admin.ModelAdmin):
    list_display = ['court', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['court__name', 'user__username', 'comment']
