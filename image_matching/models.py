from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ImageVector(models.Model):
    """Görüntü vektörleri için model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_vectors')
    image_path = models.CharField(max_length=500)
    vector_id = models.CharField(max_length=100, unique=True)  # Milvus'taki vector ID
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_found = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'image_vectors'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Image Vector {self.vector_id}"


class ImageMatch(models.Model):
    """Görüntü eşleştirme sonuçları"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_vector = models.ForeignKey(ImageVector, on_delete=models.CASCADE, related_name='source_matches')
    target_vector = models.ForeignKey(ImageVector, on_delete=models.CASCADE, related_name='target_matches')
    similarity_score = models.FloatField()
    match_confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'image_matches'
        ordering = ['-similarity_score']
        unique_together = ['source_vector', 'target_vector']
    
    def __str__(self):
        return f"Match: {self.source_vector.vector_id} -> {self.target_vector.vector_id}"


class ImageProcessingJob(models.Model):
    """Görüntü işleme işleri"""
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processing_jobs')
    image_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'image_processing_jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Processing Job {self.id} - {self.status}"
