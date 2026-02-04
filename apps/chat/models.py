# app: chat/models.py
from django.conf import settings
from django.db import models
from apps.projects.models import FormDefinition, FormData
from django.contrib.auth.models import User
import uuid


class Conversation(models.Model):
    """
    A conversation (chat room) with 2+ participants.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title        = models.CharField(max_length=255, blank=True, null=True)
    form         = models.ForeignKey(FormDefinition, related_name="form_conversation", on_delete=models.CASCADE)
    instance     = models.ForeignKey(FormData, related_name="form_instance", on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name="conversations")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    created_by   = models.ForeignKey(User, related_name="created_conversations", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.title:
            return self.title
        return f"Conversation #{self.pk}"
    
    class Meta:
        db_table = 'chat_conversations'
        managed = True
        verbose_name = "Conversation"
        verbose_name_plural = "1. Conversations"


class Message(models.Model):
    """
    Individual message in a conversation.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation,related_name="messages",on_delete=models.CASCADE)
    sender       = models.ForeignKey(User,related_name="sent_messages", on_delete=models.CASCADE)
    external_id  = models.CharField(max_length = 150, null=True, blank=True, unique=True, db_index=True)
    language_code = models.CharField(max_length = 10, null=True, blank=True, default="en")
    text         = models.TextField()
    created_at   = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation.id}"
    

    class Meta:
        db_table = 'chat_messages'
        managed = True
        verbose_name = "Message"
        verbose_name_plural = "1. Messages"