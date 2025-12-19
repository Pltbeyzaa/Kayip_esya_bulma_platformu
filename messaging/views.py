from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
import json
from .services import ChatService, NotificationService
from .models import ChatRoom, Message, Notification, UserDevice, ChatInvitation, ChatRoomMembership

User = get_user_model()


class ChatAPIView(View):
    """Sohbet API"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Sohbet odası oluştur"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            room_type = data.get('room_type', 'general')
            
            if not name:
                return JsonResponse({'error': 'Room name required'}, status=400)
            
            room = self.chat_service.create_room(
                name=name,
                description=description,
                created_by_id=str(request.user.id),
                room_type=room_type
            )
            
            if room:
                return JsonResponse({
                    'success': True,
                    'room': {
                        'id': str(room.id),
                        'name': room.name,
                        'description': room.description,
                        'room_type': room.room_type,
                        'created_at': room.created_at.isoformat()
                    }
                })
            else:
                return JsonResponse({'error': 'Failed to create room'}, status=500)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
def start_chat_with_user(request, user_id: int):
    """
    Bir kullanıcı ile (ilan sahibi gibi) ikili sohbet başlat veya mevcut odaya yönlendir.
    """
    target_user = get_object_or_404(User, id=user_id)

    # Kendisiyle sohbet açmaya çalışıyorsa profile dön
    if target_user.id == request.user.id:
        return redirect('profile')

    chat_service = ChatService()

    # Mevcut ikili oda var mı? (item_match tipinde)
    existing_room = (
        ChatRoom.objects
        .filter(room_type='item_match', is_active=True, participants=request.user)
        .filter(participants=target_user)
        .first()
    )

    if not existing_room:
        # Yeni oda oluştur
        room_name = f"{request.user.first_name or request.user.username} & {target_user.first_name or target_user.username}"
        description = "Eşleşen ilanlar için özel sohbet odası"

        room = chat_service.create_room(
            name=room_name,
            description=description,
            created_by_id=str(request.user.id),
            room_type='item_match',
        )

        if room:
            # Diğer kullanıcıyı da katılımcı olarak ekle
            ChatRoomMembership.objects.get_or_create(
                room=room,
                user=target_user,
                defaults={'role': 'member'},
            )
            # MongoDB / Firebase tarafını güncelle
            chat_service._save_room_to_mongodb(room)  # mevcut yardımcıyı yeniden kullan

            existing_room = room

    if not existing_room:
        # Her ihtimale karşı oda oluşturulamadıysa ana sayfaya dön
        return redirect('home')

    return redirect('chat_room', room_id=existing_room.id)


@login_required
def chat_room(request, room_id):
    """
    Basit web arayüzü ile sohbet odası.
    Mesajlar Django üzerinden gelir, gönderilen her mesaj Firebase/Mongo'ya da yazılır.
    """
    room = get_object_or_404(
        ChatRoom.objects.prefetch_related('participants'),
        id=room_id,
        is_active=True,
    )

    # Kullanıcı bu odanın katılımcısı değilse erişimi engelle
    if not room.participants.filter(id=request.user.id).exists():
        return redirect('home')

    chat_service = ChatService()

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        if content:
            chat_service.send_message(
                room_id=str(room.id),
                sender_id=str(request.user.id),
                content=content,
                message_type='text',
            )
        return redirect('chat_room', room_id=room.id)

    # Son mesajları getir (en fazla 50)
    chat_messages = chat_service.get_room_messages(
        room_id=str(room.id),
        user_id=str(request.user.id),
        limit=50,
        offset=0,
    )
    # Eski → yeni sıralı gelsin
    chat_messages = list(sorted(chat_messages, key=lambda m: m['created_at']))

    from django.conf import settings
    
    return render(
        request,
        'messaging/chat_room.html',
        {
            'room': room,
            'chat_messages': chat_messages,
            'FIREBASE_API_KEY': getattr(settings, 'FIREBASE_API_KEY', ''),
            'FIREBASE_AUTH_DOMAIN': getattr(settings, 'FIREBASE_AUTH_DOMAIN', ''),
            'FIREBASE_DATABASE_URL': getattr(settings, 'FIREBASE_DATABASE_URL', ''),
            'FIREBASE_PROJECT_ID': getattr(settings, 'FIREBASE_PROJECT_ID', ''),
            'FIREBASE_STORAGE_BUCKET': getattr(settings, 'FIREBASE_STORAGE_BUCKET', ''),
            'FIREBASE_MESSAGING_SENDER_ID': getattr(settings, 'FIREBASE_MESSAGING_SENDER_ID', ''),
            'FIREBASE_APP_ID': getattr(settings, 'FIREBASE_APP_ID', ''),
        },
    )


@login_required
def conversations_list(request):
    """
    Kullanıcının dahil olduğu tüm sohbet odalarını listele.
    """
    rooms = (
        ChatRoom.objects
        .filter(participants=request.user, is_active=True)
        .prefetch_related('participants')
        .order_by('-updated_at')
    )

    conversations = []
    for room in rooms:
        last_message = (
            Message.objects
            .filter(room=room)
            .order_by('-created_at')
            .select_related('sender')
            .first()
        )

        # Karşı tarafın adını bul (tekli odalarda)
        others = room.participants.exclude(id=request.user.id)
        other_display = others.first().first_name or others.first().username if others.exists() else room.name

        conversations.append({
            'id': room.id,
            'name': other_display,
            'full_name': room.name,
            'updated_at': room.updated_at,
            'last_message': last_message.content if last_message else '',
            'last_time': last_message.created_at.strftime("%H:%M") if last_message else '',
        })

    return render(
        request,
        'messaging/conversations.html',
        {
            'conversations': conversations,
        },
    )


@login_required
@require_POST
def delete_conversation(request, room_id):
    """
    Kullanıcının kendi sohbet listesinden bir sohbeti silmesi (üyeliğini kaldırma).
    Diğer katılımcıların sohbeti etkilenmez.
    """
    room = get_object_or_404(
        ChatRoom.objects.prefetch_related('participants'),
        id=room_id,
        is_active=True,
    )

    # Kullanıcı bu odanın katılımcısı değilse sessizce geri dön
    if not room.participants.filter(id=request.user.id).exists():
        return redirect('conversations')

    # Kullanıcının üyeliğini kaldır
    ChatRoomMembership.objects.filter(room=room, user=request.user).delete()

    # Eğer odada hiç katılımcı kalmadıysa odayı pasifleştir
    if room.participants.count() == 0:
        room.is_active = False
        room.save(update_fields=['is_active'])

    return redirect('conversations')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """Mesaj gönder"""
    try:
        room_id = request.data.get('room_id')
        content = request.data.get('content')
        message_type = request.data.get('message_type', 'text')
        reply_to_id = request.data.get('reply_to_id')
        
        if not room_id or not content:
            return Response({'error': 'room_id and content required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        chat_service = ChatService()
        message = chat_service.send_message(
            room_id=room_id,
            sender_id=str(request.user.id),
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id
        )
        
        if message:
            return Response({
                'success': True,
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'message_type': message.message_type,
                    'sender': {
                        'id': str(message.sender.id),
                        'username': message.sender.username,
                        'first_name': message.sender.first_name
                    },
                    'created_at': message.created_at.isoformat(),
                    'reply_to': str(message.reply_to.id) if message.reply_to else None
                }
            })
        else:
            return Response({'error': 'Failed to send message'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_room_messages(request):
    """Oda mesajlarını getir"""
    try:
        room_id = request.GET.get('room_id')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        if not room_id:
            return Response({'error': 'room_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        chat_service = ChatService()
        messages = chat_service.get_room_messages(
            room_id=room_id,
            user_id=str(request.user.id),
            limit=limit,
            offset=offset
        )
        
        return Response({
            'success': True,
            'messages': messages,
            'total_count': len(messages)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_rooms(request):
    """Kullanıcının sohbet odalarını getir"""
    try:
        rooms = ChatRoom.objects.filter(
            participants=request.user,
            is_active=True
        ).order_by('-updated_at')
        
        rooms_list = []
        for room in rooms:
            # Son mesajı al
            last_message = Message.objects.filter(room=room).order_by('-created_at').first()
            
            rooms_list.append({
                'id': str(room.id),
                'name': room.name,
                'description': room.description,
                'room_type': room.room_type,
                'participants_count': room.participants.count(),
                'last_message': {
                    'content': last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else "",
                    'sender': last_message.sender.username if last_message else "",
                    'created_at': last_message.created_at.isoformat() if last_message else None
                } if last_message else None,
                'created_at': room.created_at.isoformat(),
                'updated_at': room.updated_at.isoformat()
            })
        
        return Response({
            'success': True,
            'rooms': rooms_list,
            'total_count': len(rooms_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_room(request):
    """Sohbet odası oluştur"""
    try:
        name = request.data.get('name')
        description = request.data.get('description', '')
        room_type = request.data.get('room_type', 'general')
        
        if not name:
            return Response({'error': 'Room name required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        chat_service = ChatService()
        room = chat_service.create_room(
            name=name,
            description=description,
            created_by_id=str(request.user.id),
            room_type=room_type
        )
        
        if room:
            return Response({
                'success': True,
                'room': {
                    'id': str(room.id),
                    'name': room.name,
                    'description': room.description,
                    'room_type': room.room_type,
                    'created_at': room.created_at.isoformat()
                }
            })
        else:
            return Response({'error': 'Failed to create room'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_to_room(request):
    """Kullanıcıyı odaya davet et"""
    try:
        room_id = request.data.get('room_id')
        invitee_id = request.data.get('invitee_id')
        message = request.data.get('message', '')
        
        if not room_id or not invitee_id:
            return Response({'error': 'room_id and invitee_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        chat_service = ChatService()
        invitation = chat_service.invite_user_to_room(
            room_id=room_id,
            inviter_id=str(request.user.id),
            invitee_id=invitee_id,
            message=message
        )
        
        if invitation:
            return Response({
                'success': True,
                'invitation': {
                    'id': str(invitation.id),
                    'room_name': invitation.room.name,
                    'inviter': invitation.inviter.username,
                    'invitee': invitation.invitee.username,
                    'message': invitation.message,
                    'status': invitation.status,
                    'expires_at': invitation.expires_at.isoformat(),
                    'created_at': invitation.created_at.isoformat()
                }
            })
        else:
            return Response({'error': 'Failed to send invitation'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Kullanıcı bildirimlerini getir"""
    try:
        limit = int(request.GET.get('limit', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        
        notification_service = NotificationService()
        notifications = notification_service.get_user_notifications(
            user_id=str(request.user.id),
            limit=limit,
            unread_only=unread_only
        )
        
        return Response({
            'success': True,
            'notifications': notifications,
            'total_count': len(notifications)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    """Kullanıcının okunmamış mesaj gönderen kişi sayısını getir"""
    try:
        from messaging.models import ChatRoom, Message, MessageRead
        
        # Kullanıcının katıldığı aktif odalar
        user_rooms = ChatRoom.objects.filter(
            participants=request.user,
            is_active=True
        )
        
        # Farklı gönderen ID'lerini topla
        unique_senders = set()
        
        for room in user_rooms:
            # Bu odadaki, kullanıcının göndermediği mesajlar
            unread_messages = Message.objects.filter(
                room=room
            ).exclude(
                sender=request.user
            )
            
            # Okunmuş mesajları çıkar
            read_message_ids = MessageRead.objects.filter(
                user=request.user,
                message__room=room
            ).values_list('message_id', flat=True)
            
            unread_messages = unread_messages.exclude(id__in=read_message_ids)
            
            # Bu odadaki okunmamış mesajların gönderenlerini ekle
            sender_ids = unread_messages.values_list('sender_id', flat=True).distinct()
            unique_senders.update(sender_ids)
        
        unread_count = len(unique_senders)
        
        return Response({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'unread_count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_room_messages_read(request):
    """Oda açıldığında tüm mesajları okundu olarak işaretle"""
    try:
        room_id = request.data.get('room_id')
        if not room_id:
            return Response({'error': 'room_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        from messaging.models import ChatRoom, Message, MessageRead
        
        room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
        
        # Kullanıcı bu odanın katılımcısı mı kontrol et
        if not room.participants.filter(id=request.user.id).exists():
            return Response({'error': 'Not a participant'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Bu odadaki, kullanıcının göndermediği tüm mesajları okundu olarak işaretle
        unread_messages = Message.objects.filter(
            room=room
        ).exclude(
            sender=request.user
        )
        
        # Okunmuş mesajları çıkar
        read_message_ids = MessageRead.objects.filter(
            user=request.user,
            message__room=room
        ).values_list('message_id', flat=True)
        
        unread_messages = unread_messages.exclude(id__in=read_message_ids)
        
        # Okunmamış mesajları okundu olarak işaretle
        for message in unread_messages:
            MessageRead.objects.get_or_create(
                message=message,
                user=request.user
            )
        
        return Response({
            'success': True,
            'marked_count': unread_messages.count()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    """Bildirimi okundu olarak işaretle"""
    try:
        notification_id = request.data.get('notification_id')
        
        if not notification_id:
            return Response({'error': 'notification_id required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        notification_service = NotificationService()
        success = notification_service.mark_notification_as_read(
            notification_id=notification_id,
            user_id=str(request.user.id)
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return Response({'error': 'Failed to mark notification as read'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device(request):
    """Cihaz kaydet (FCM için)"""
    try:
        device_id = request.data.get('device_id')
        device_type = request.data.get('device_type')
        fcm_token = request.data.get('fcm_token')
        
        if not device_id or not device_type:
            return Response({'error': 'device_id and device_type required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        device, created = UserDevice.objects.get_or_create(
            user=request.user,
            device_id=device_id,
            defaults={
                'device_type': device_type,
                'fcm_token': fcm_token,
                'is_active': True
            }
        )
        
        if not created:
            device.fcm_token = fcm_token
            device.is_active = True
            device.save()
        
        return Response({
            'success': True,
            'message': 'Device registered successfully',
            'device': {
                'id': str(device.id),
                'device_id': device.device_id,
                'device_type': device.device_type,
                'is_active': device.is_active,
                'created_at': device.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
