from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom User model"""
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'accounts_user'
    
    def __str__(self):
        return self.email


class ItemPost(models.Model):
    """İlan modeli - Kayıp ve bulunan eşyalar için"""
    
    POST_TYPES = [
        ('lost', 'Kayıp Eşya'),
        ('found', 'Bulunan Eşya'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('resolved', 'Çözüldü'),
        ('closed', 'Kapalı'),
    ]
    
    # Temel bilgiler
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(verbose_name="Açıklama")
    post_type = models.CharField(max_length=10, choices=POST_TYPES, verbose_name="İlan Türü")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Durum")
    
    # Konum bilgileri
    location = models.CharField(max_length=200, verbose_name="Konum")
    city = models.CharField(max_length=100, verbose_name="Şehir")
    district = models.CharField(max_length=100, verbose_name="İlçe", blank=True, null=True)
    
    # İletişim bilgileri
    contact_phone = models.CharField(max_length=15, verbose_name="İletişim Telefonu")
    contact_email = models.EmailField(verbose_name="İletişim E-posta", blank=True, null=True)
    
    # Görsel ve dosyalar
    image = models.ImageField(upload_to='item_images/', blank=True, null=True, verbose_name="Görsel")
    
    # Kullanıcı ve tarih bilgileri
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='item_posts', verbose_name="Kullanıcı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    # Ekstra alanlar
    is_urgent = models.BooleanField(default=False, verbose_name="Acil")
    
    # Kayıp çocuk ilanları için özel alanlar
    is_missing_child = models.BooleanField(default=False, verbose_name="Kayıp Çocuk İlanı")
    child_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Çocuğun Adı")
    child_age = models.IntegerField(blank=True, null=True, verbose_name="Yaş")
    child_gender = models.CharField(
        max_length=10,
        choices=[('erkek', 'Erkek'), ('kız', 'Kız')],
        blank=True,
        null=True,
        verbose_name="Cinsiyet"
    )
    child_height = models.IntegerField(blank=True, null=True, verbose_name="Boy (cm)")
    child_weight = models.IntegerField(blank=True, null=True, verbose_name="Kilo (kg)")
    child_hair_color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Saç Rengi")
    child_eye_color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Göz Rengi")
    child_physical_features = models.TextField(blank=True, null=True, verbose_name="Fiziksel Özellikler")
    missing_date = models.DateField(blank=True, null=True, verbose_name="Kaybolma Tarihi")
    last_seen_location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Son Görüldüğü Yer")
    last_seen_clothing = models.TextField(blank=True, null=True, verbose_name="Son Görüldüğünde Üzerindeki Kıyafetler")
    
    class Meta:
        db_table = 'accounts_itempost'
        ordering = ['-created_at']
        verbose_name = "İlan"
        verbose_name_plural = "İlanlar"
    
    def __str__(self):
        return f"{self.get_post_type_display()} - {self.title}"
    
    @property
    def is_recent(self):
        """Son 7 gün içinde oluşturulmuş mu?"""
        return (timezone.now() - self.created_at).days <= 7
    
    @property
    def days_ago(self):
        """Kaç gün önce oluşturulmuş?"""
        return (timezone.now() - self.created_at).days
