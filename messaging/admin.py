from django.contrib import admin
from .models import ChatRoom, ChatRoomMembership, Message, MessageRead, Notification, UserDevice, ChatInvitation


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__email', 'created_by__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)
    date_hierarchy = 'created_at'


@admin.register(ChatRoomMembership)
class ChatRoomMembershipAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'role', 'is_muted', 'is_banned', 'joined_at')
    list_filter = ('role', 'is_muted', 'is_banned', 'joined_at')
    search_fields = ('room__name', 'user__email', 'user__username')
    readonly_fields = ('joined_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'message_type', 'created_at', 'is_edited')
    list_filter = ('message_type', 'is_edited', 'created_at')
    search_fields = ('content', 'room__name', 'sender__email', 'sender__username')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('message__content', 'user__email', 'user__username')
    readonly_fields = ('read_at',)
    date_hierarchy = 'read_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'user', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'created_at')
    search_fields = ('title', 'message', 'user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'sent_at')
    date_hierarchy = 'created_at'


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'device_id', 'is_active', 'last_seen', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__username', 'device_id', 'fcm_token')
    readonly_fields = ('created_at', 'last_seen')


@admin.register(ChatInvitation)
class ChatInvitationAdmin(admin.ModelAdmin):
    list_display = ('room', 'inviter', 'invitee', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('room__name', 'inviter__email', 'invitee__email', 'message')
    readonly_fields = ('id', 'created_at', 'responded_at')
    date_hierarchy = 'created_at'

