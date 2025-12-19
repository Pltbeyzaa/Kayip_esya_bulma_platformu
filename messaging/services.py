"""
Mesajlaşma servisleri
Firebase API → MongoDB entegrasyonu
"""
import json
import firebase_admin
from firebase_admin import credentials, messaging, db
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone
from kayip_esya.mongodb import get_collection, get_db
from .models import ChatRoom, Message, Notification, UserDevice, ChatInvitation, MessageRead, ChatRoomMembership


class FirebaseService:
    """Firebase Cloud Messaging servisi"""
    
    def __init__(self):
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Firebase'i başlat"""
        try:
            # Zaten initialize edilmişse tekrar etme
            try:
                self.app = firebase_admin.get_app()
                return
            except ValueError:
                # Henüz initialize edilmemiş, devam et
                pass
            
            if settings.FIREBASE_CREDENTIALS_PATH:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                options = {}
                if settings.FIREBASE_DATABASE_URL:
                    options['databaseURL'] = settings.FIREBASE_DATABASE_URL
                self.app = firebase_admin.initialize_app(cred, options)
            else:
                print("Firebase credentials not configured")
        except Exception as e:
            print(f"Firebase initialization error: {e}")
    
    def send_notification(self, user_id: str, title: str, body: str, 
                         data: Dict = None) -> bool:
        """Kullanıcıya bildirim gönder"""
        try:
            if not self.app:
                return False
            
            # Kullanıcının aktif cihazlarını al
            devices = UserDevice.objects.filter(
                user_id=user_id, 
                is_active=True,
                fcm_token__isnull=False
            )
            
            if not devices.exists():
                return False
            
            # Her cihaza bildirim gönder
            for device in devices:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data=data or {},
                    token=device.fcm_token
                )
                
                try:
                    messaging.send(message)
                except Exception as e:
                    print(f"FCM send error for device {device.device_id}: {e}")
                    # Cihaz token'ı geçersizse deaktive et
                    device.is_active = False
                    device.save()
            
            return True
            
        except Exception as e:
            print(f"Firebase notification error: {e}")
            return False
    
    def send_multicast_notification(self, user_ids: List[str], title: str, 
                                   body: str, data: Dict = None) -> bool:
        """Birden fazla kullanıcıya bildirim gönder"""
        try:
            if not self.app:
                return False
            
            # Tüm aktif cihazları al
            devices = UserDevice.objects.filter(
                user_id__in=user_ids,
                is_active=True,
                fcm_token__isnull=False
            )
            
            if not devices.exists():
                return False
            
            tokens = list(devices.values_list('fcm_token', flat=True))
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            print(f"Successfully sent {response.success_count} notifications")
            
            return True
            
        except Exception as e:
            print(f"Firebase multicast notification error: {e}")
            return False


class ChatService:
    """Sohbet servisi"""
    
    def __init__(self):
        self.firebase = FirebaseService()
    
    def create_room(self, name: str, description: str, created_by_id: str, 
                   room_type: str = 'general') -> Optional[ChatRoom]:
        """Sohbet odası oluştur ve MongoDB'ye kaydet"""
        try:
            room = ChatRoom.objects.create(
                name=name,
                description=description,
                created_by_id=created_by_id,
                room_type=room_type
            )
            
            # Oluşturan kişiyi admin olarak ekle
            ChatRoomMembership.objects.create(
                room=room,
                user_id=created_by_id,
                role='admin'
            )
            
            # MongoDB'ye kaydet
            self._save_room_to_mongodb(room)
            
            return room
            
        except Exception as e:
            print(f"Room creation error: {e}")
            return None
    
    def _save_room_to_mongodb(self, room: ChatRoom):
        """Sohbet odasını MongoDB'ye kaydet"""
        try:
            rooms_collection = get_collection('chat_rooms')
            
            room_data = {
                'room_id': str(room.id),
                'name': room.name,
                'description': room.description,
                'room_type': room.room_type,
                'created_by_id': str(room.created_by.id),
                'created_by_username': room.created_by.username,
                'is_active': room.is_active,
                'created_at': room.created_at.isoformat(),
                'updated_at': room.updated_at.isoformat(),
                'participants': [str(p.id) for p in room.participants.all()]
            }
            
            # MongoDB'ye ekle veya güncelle
            rooms_collection.update_one(
                {'room_id': str(room.id)},
                {'$set': room_data},
                upsert=True
            )
            
            # Firebase Realtime Database'e de kaydet (opsiyonel)
            if self.firebase.app and settings.FIREBASE_DATABASE_URL:
                try:
                    ref = db.reference(f'rooms/{room.id}')
                    ref.set(room_data)
                except Exception as e:
                    print(f"Firebase Realtime DB save error: {e}")
            
        except Exception as e:
            print(f"MongoDB room save error: {e}")
    
    def send_message(self, room_id: str, sender_id: str, content: str, 
                    message_type: str = 'text', reply_to_id: str = None) -> Optional[Message]:
        """Mesaj gönder ve MongoDB'ye kaydet"""
        try:
            room = ChatRoom.objects.get(id=room_id)
            
            # Kullanıcının odada olup olmadığını kontrol et
            if not room.participants.filter(id=sender_id).exists():
                return None
            
            # Django model'de kaydet
            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                content=content,
                message_type=message_type,
                reply_to_id=reply_to_id
            )
            
            # MongoDB'ye kaydet (Firebase API ile entegre)
            self._save_message_to_mongodb(message)
            
            # Odadaki diğer kullanıcılara bildirim gönder
            self._notify_room_participants(room, message, sender_id)
            
            return message
            
        except Exception as e:
            print(f"Message sending error: {e}")
            return None
    
    def _save_message_to_mongodb(self, message: Message):
        """Mesajı MongoDB'ye kaydet"""
        try:
            messages_collection = get_collection('messages')
            
            # Mesaj verilerini hazırla
            message_data = {
                'message_id': str(message.id),
                'room_id': str(message.room.id),
                'sender_id': str(message.sender.id),
                'sender_username': message.sender.username,
                'sender_name': f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip() or message.sender.username,
                'content': message.content,
                'message_type': message.message_type,
                'attachment_url': message.attachment_url or None,
                'attachment_name': message.attachment_name or None,
                'is_edited': message.is_edited,
                'edited_at': message.edited_at.isoformat() if message.edited_at else None,
                'reply_to_id': str(message.reply_to.id) if message.reply_to else None,
                'created_at': message.created_at.isoformat(),
                'room_name': message.room.name,
                'room_type': message.room.room_type
            }
            
            # MongoDB'ye ekle
            messages_collection.insert_one(message_data)
            
            # Firebase Realtime Database'e de kaydet (opsiyonel)
            if self.firebase.app and settings.FIREBASE_DATABASE_URL:
                try:
                    ref = db.reference(f'messages/{message.room.id}')
                    ref.push(message_data)
                except Exception as e:
                    print(f"Firebase Realtime DB save error: {e}")
            
        except Exception as e:
            print(f"MongoDB message save error: {e}")
    
    def _notify_room_participants(self, room: ChatRoom, message: Message, sender_id: str):
        """Oda katılımcılarına bildirim gönder"""
        try:
            # Gönderen hariç diğer katılımcıları al
            participants = room.participants.exclude(id=sender_id)
            
            for participant in participants:
                # Bildirim oluştur
                notification = Notification.objects.create(
                    user=participant,
                    notification_type='message',
                    title=f"Yeni mesaj: {room.name}",
                    message=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                    data={
                        'room_id': str(room.id),
                        'message_id': str(message.id),
                        'sender_name': message.sender.first_name or message.sender.username
                    }
                )
                
                # FCM bildirimi gönder
                self.firebase.send_notification(
                    user_id=str(participant.id),
                    title=f"Yeni mesaj: {room.name}",
                    body=message.content[:100] + "..." if len(message.content) > 100 else message.content,
                    data={
                        'type': 'message',
                        'room_id': str(room.id),
                        'message_id': str(message.id)
                    }
                )
                
        except Exception as e:
            print(f"Room notification error: {e}")
    
    def get_room_messages(self, room_id: str, user_id: str, limit: int = 50, 
                         offset: int = 0) -> List[Dict]:
        """Oda mesajlarını getir"""
        try:
            room = ChatRoom.objects.get(id=room_id)
            
            # Kullanıcının odada olup olmadığını kontrol et
            if not room.participants.filter(id=user_id).exists():
                return []
            
            messages = Message.objects.filter(room=room).order_by('-created_at')[offset:offset+limit]
            
            message_list = []
            for message in messages:
                message_list.append({
                    'id': str(message.id),
                    'content': message.content,
                    'message_type': message.message_type,
                    'sender': {
                        'id': str(message.sender.id),
                        'username': message.sender.username,
                        'first_name': message.sender.first_name,
                        'last_name': message.sender.last_name
                    },
                    'created_at': message.created_at.isoformat(),
                    'time': message.created_at.strftime("%H:%M"),
                    'is_edited': message.is_edited,
                    'is_me': str(message.sender.id) == str(user_id),
                    'reply_to': {
                        'id': str(message.reply_to.id),
                        'content': message.reply_to.content[:50] + "..."
                    } if message.reply_to else None
                })
            
            return message_list
            
        except Exception as e:
            print(f"Get room messages error: {e}")
            return []
    
    def mark_message_as_read(self, message_id: str, user_id: str) -> bool:
        """Mesajı okundu olarak işaretle"""
        try:
            message = Message.objects.get(id=message_id)
            
            # Okuma kaydı oluştur veya güncelle
            MessageRead.objects.get_or_create(
                message=message,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            print(f"Mark message as read error: {e}")
            return False
    
    def invite_user_to_room(self, room_id: str, inviter_id: str, invitee_id: str, 
                           message: str = None) -> Optional[ChatInvitation]:
        """Kullanıcıyı odaya davet et"""
        try:
            room = ChatRoom.objects.get(id=room_id)
            
            # Davet eden kişinin odada olup olmadığını kontrol et
            if not room.participants.filter(id=inviter_id).exists():
                return None
            
            # Zaten üye mi kontrol et
            if room.participants.filter(id=invitee_id).exists():
                return None
            
            # Davet oluştur
            invitation = ChatInvitation.objects.create(
                room=room,
                inviter_id=inviter_id,
                invitee_id=invitee_id,
                message=message,
                expires_at=timezone.now() + timezone.timedelta(days=7)  # 7 gün geçerli
            )
            
            # Davet edilen kişiye bildirim gönder
            self.firebase.send_notification(
                user_id=invitee_id,
                title=f"Davet: {room.name}",
                body=f"{room.created_by.first_name or room.created_by.username} sizi bir sohbete davet etti.",
                data={
                    'type': 'invitation',
                    'room_id': str(room.id),
                    'invitation_id': str(invitation.id)
                }
            )
            
            return invitation
            
        except Exception as e:
            print(f"Invite user error: {e}")
            return None


class NotificationService:
    """Bildirim servisi"""
    
    def __init__(self):
        self.firebase = FirebaseService()
    
    def create_notification(self, user_id: str, notification_type: str, 
                          title: str, message: str, data: Dict = None) -> Notification:
        """Bildirim oluştur"""
        try:
            notification = Notification.objects.create(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {}
            )
            
            # MongoDB'ye kaydet
            self._save_notification_to_mongodb(notification)
            
            # FCM bildirimi gönder
            self.firebase.send_notification(
                user_id=user_id,
                title=title,
                body=message,
                data={
                    'type': notification_type,
                    'notification_id': str(notification.id)
                }
            )
            
            return notification
            
        except Exception as e:
            print(f"Create notification error: {e}")
            return None
    
    def _save_notification_to_mongodb(self, notification: Notification):
        """Bildirimi MongoDB'ye kaydet"""
        try:
            notifications_collection = get_collection('notifications')
            
            notification_data = {
                'notification_id': str(notification.id),
                'user_id': str(notification.user.id),
                'user_username': notification.user.username,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'is_read': notification.is_read,
                'is_sent': notification.is_sent,
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'created_at': notification.created_at.isoformat()
            }
            
            # MongoDB'ye ekle
            notifications_collection.insert_one(notification_data)
            
            # Firebase Realtime Database'e de kaydet (opsiyonel)
            if self.firebase.app and settings.FIREBASE_DATABASE_URL:
                try:
                    ref = db.reference(f'notifications/{notification.user.id}')
                    ref.push(notification_data)
                except Exception as e:
                    print(f"Firebase Realtime DB save error: {e}")
            
        except Exception as e:
            print(f"MongoDB notification save error: {e}")
    
    def send_match_notification(self, user_id: str, match_type: str, 
                               item_title: str, match_details: Dict) -> bool:
        """Eşleşme bildirimi gönder"""
        try:
            title = f"Yeni Eşleşme: {item_title}"
            message = f"{match_type} için yeni bir eşleşme bulundu!"
            
            notification = self.create_notification(
                user_id=user_id,
                notification_type='match',
                title=title,
                message=message,
                data=match_details
            )
            
            return notification is not None
            
        except Exception as e:
            print(f"Match notification error: {e}")
            return False
    
    def get_user_notifications(self, user_id: str, limit: int = 20, 
                              unread_only: bool = False) -> List[Dict]:
        """Kullanıcı bildirimlerini getir"""
        try:
            notifications = Notification.objects.filter(user_id=user_id)
            
            if unread_only:
                notifications = notifications.filter(is_read=False)
            
            notifications = notifications.order_by('-created_at')[:limit]
            
            notification_list = []
            for notification in notifications:
                notification_list.append({
                    'id': str(notification.id),
                    'type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'data': notification.data,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat()
                })
            
            return notification_list
            
        except Exception as e:
            print(f"Get user notifications error: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Bildirimi okundu olarak işaretle"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user_id=user_id
            )
            
            notification.is_read = True
            notification.save()
            
            return True
            
        except Exception as e:
            print(f"Mark notification as read error: {e}")
            return False
