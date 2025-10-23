from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ChatRoom(models.Model):
    """Sohbet odaları"""
    ROOM_TYPES = [
        ('item_match', 'Eşya Eşleştirme'),
        ('general', 'Genel Sohbet'),
        ('support', 'Destek'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    participants = models.ManyToManyField(User, related_name='chat_rooms', through='ChatRoomMembership')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_rooms'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat Room: {self.name}"


class ChatRoomMembership(models.Model):
    """Sohbet odası üyelikleri"""
    ROLE_CHOICES = [
        ('admin', 'Yönetici'),
        ('moderator', 'Moderatör'),
        ('member', 'Üye'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'chat_room_memberships'
        unique_together = ['room', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"


class Message(models.Model):
    """Mesajlar"""
    MESSAGE_TYPES = [
        ('text', 'Metin'),
        ('image', 'Resim'),
        ('file', 'Dosya'),
        ('location', 'Konum'),
        ('system', 'Sistem'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    attachment_url = models.URLField(blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    attachment_size = models.BigIntegerField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.room.name}"


class MessageRead(models.Model):
    """Mesaj okuma durumları"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_reads'
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class Notification(models.Model):
    """Bildirimler"""
    NOTIFICATION_TYPES = [
        ('message', 'Mesaj'),
        ('match', 'Eşleşme'),
        ('system', 'Sistem'),
        ('reminder', 'Hatırlatma'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Ek veri
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class UserDevice(models.Model):
    """Kullanıcı cihazları (FCM için)"""
    DEVICE_TYPES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    fcm_token = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_devices'
        unique_together = ['user', 'device_id']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class ChatInvitation(models.Model):
    """Sohbet davetleri"""
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('accepted', 'Kabul Edildi'),
        ('declined', 'Reddedildi'),
        ('expired', 'Süresi Doldu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_invitations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation: {self.inviter.username} -> {self.invitee.username}"
