from django.contrib import admin
from .models import ImageVector, ImageMatch, ImageProcessingJob


@admin.register(ImageVector)
class ImageVectorAdmin(admin.ModelAdmin):
    list_display = ('vector_id', 'user', 'image_path', 'is_found', 'created_at')
    list_filter = ('is_found', 'created_at')
    search_fields = ('vector_id', 'user__email', 'user__username', 'description', 'image_path')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(ImageMatch)
class ImageMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_vector', 'target_vector', 'similarity_score', 'match_confidence', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('source_vector__vector_id', 'target_vector__vector_id', 'verified_by__email')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(ImageProcessingJob)
class ImageProcessingJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username', 'image_path', 'error_message')
    readonly_fields = ('id', 'created_at', 'completed_at')
    date_hierarchy = 'created_at'

