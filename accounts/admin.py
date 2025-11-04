from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ItemPost


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('İzinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Önemli Tarihler', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(ItemPost)
class ItemPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_type', 'status', 'user', 'city', 'created_at', 'is_urgent')
    list_filter = ('post_type', 'status', 'city', 'is_urgent', 'created_at')
    search_fields = ('title', 'description', 'location', 'city', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Temel Bilgiler', {'fields': ('title', 'description', 'post_type', 'status', 'user')}),
        ('Konum Bilgileri', {'fields': ('location', 'city', 'district')}),
        ('İletişim', {'fields': ('contact_phone', 'contact_email')}),
        ('Görsel', {'fields': ('image',)}),
        ('Diğer', {'fields': ('is_urgent', 'created_at', 'updated_at')}),
    )
