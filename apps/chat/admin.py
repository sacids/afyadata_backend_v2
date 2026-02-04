# app: chat/admin.py

from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    """
    Inline messages inside a conversation view (read-only text).
    """

    model = Message
    extra = 0
    fields = ("sender", "text", "language_code", "is_read", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("created_at",)
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "form",
        "instance",
        "participant_count",
        "created_by",
        "updated_at",
    )
    list_filter = ("form", "created_at", "updated_at")
    search_fields = ("title", "id")
    ordering = ("-updated_at",)
    filter_horizontal = ("participants",)

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Conversation Details", {"fields": ("id", "title", "form", "instance")}),
        ("Participants", {"fields": ("participants", "created_by")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    inlines = [MessageInline]

    def participant_count(self, obj):
        return obj.participants.count()

    participant_count.short_description = "Participants"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "short_text",
        "conversation",
        "sender",
        "language_code",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "language_code", "created_at")
    search_fields = ("text", "sender__username", "conversation__id")
    ordering = ("created_at",)

    readonly_fields = ("id", "created_at")

    fieldsets = (
        (
            "Message Details",
            {"fields": ("id", "conversation", "sender", "external_id")},
        ),
        ("Content", {"fields": ("text", "language_code", "is_read")}),
        ("Timestamp", {"fields": ("created_at",)}),
    )

    def short_text(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")

    short_text.short_description = "Message"
