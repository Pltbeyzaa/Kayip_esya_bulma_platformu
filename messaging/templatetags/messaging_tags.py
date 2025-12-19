from django import template
from messaging.models import ChatRoom, Message, MessageRead

register = template.Library()


@register.simple_tag
def unread_message_count(user):
    """
    Kullanıcının okunmamış mesaj gönderen kişi sayısını hesaplar.
    Kullanıcının katıldığı odalardaki, kendisinin göndermediği ve okumadığı mesajları gönderen
    farklı kişi sayısını döndürür.
    """
    if not user or not user.is_authenticated:
        return 0
    
    # Kullanıcının katıldığı aktif odalar
    user_rooms = ChatRoom.objects.filter(
        participants=user,
        is_active=True
    )
    
    # Farklı gönderen ID'lerini topla
    unique_senders = set()
    
    for room in user_rooms:
        # Bu odadaki, kullanıcının göndermediği mesajlar
        unread_messages = Message.objects.filter(
            room=room
        ).exclude(
            sender=user
        )
        
        # Okunmuş mesajları çıkar
        read_message_ids = MessageRead.objects.filter(
            user=user,
            message__room=room
        ).values_list('message_id', flat=True)
        
        unread_messages = unread_messages.exclude(id__in=read_message_ids)
        
        # Bu odadaki okunmamış mesajların gönderenlerini ekle
        sender_ids = unread_messages.values_list('sender_id', flat=True).distinct()
        unique_senders.update(sender_ids)
    
    return len(unique_senders)
