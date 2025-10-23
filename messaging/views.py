from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .services import ChatService, NotificationService
from .models import ChatRoom, Message, Notification, UserDevice, ChatInvitation


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
