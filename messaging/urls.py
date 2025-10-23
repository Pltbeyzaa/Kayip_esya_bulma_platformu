from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/chat/', views.ChatAPIView.as_view(), name='chat_api'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/room-messages/', views.get_room_messages, name='get_room_messages'),
    path('api/user-rooms/', views.get_user_rooms, name='get_user_rooms'),
    path('api/create-room/', views.create_room, name='create_room'),
    path('api/invite-to-room/', views.invite_to_room, name='invite_to_room'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/mark-notification-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/register-device/', views.register_device, name='register_device'),
]
