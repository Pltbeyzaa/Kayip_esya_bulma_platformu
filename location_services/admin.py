from django.contrib import admin
from .models import Location, LostItem, FoundItem, LocationMatch, SearchRadius


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'district', 'latitude', 'longitude', 'user', 'created_at')
    list_filter = ('city', 'country', 'created_at')
    search_fields = ('name', 'city', 'district', 'address', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'status', 'user', 'location', 'lost_date', 'created_at')
    list_filter = ('status', 'item_type', 'created_at')
    search_fields = ('title', 'description', 'item_type', 'user__email', 'location__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'status', 'user', 'location', 'found_date', 'created_at')
    list_filter = ('status', 'item_type', 'created_at')
    search_fields = ('title', 'description', 'item_type', 'user__email', 'location__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(LocationMatch)
class LocationMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'lost_item', 'found_item', 'distance_km', 'match_score', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('lost_item__title', 'found_item__title', 'verified_by__email')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(SearchRadius)
class SearchRadiusAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_radius', 'max_radius', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

