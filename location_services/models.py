from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Location(models.Model):
    """Konum bilgileri"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Turkey')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'locations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"


class LostItem(models.Model):
    """Kayıp eşya ilanları"""
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('found', 'Bulundu'),
        ('closed', 'Kapalı'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    item_type = models.CharField(max_length=100)  # Cüzdan, telefon, anahtar vb.
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='lost_items')
    lost_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lost_items'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Lost: {self.title}"


class FoundItem(models.Model):
    """Bulunan eşya ilanları"""
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('claimed', 'Sahibi Bulundu'),
        ('closed', 'Kapalı'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    item_type = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='found_items')
    found_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'found_items'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Found: {self.title}"


class LocationMatch(models.Model):
    """Konum tabanlı eşleştirmeler"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='location_matches')
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='location_matches')
    distance_km = models.FloatField()  # Kilometre cinsinden mesafe
    match_score = models.FloatField()  # Eşleşme puanı (0-1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'location_matches'
        ordering = ['-match_score']
        unique_together = ['lost_item', 'found_item']
    
    def __str__(self):
        return f"Location Match: {self.lost_item.title} <-> {self.found_item.title}"


class SearchRadius(models.Model):
    """Arama yarıçapı ayarları"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='search_radius')
    default_radius = models.FloatField(default=5.0)  # Varsayılan 5 km
    max_radius = models.FloatField(default=50.0)  # Maksimum 50 km
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'search_radius'
    
    def __str__(self):
        return f"{self.user.username} - {self.default_radius}km"
