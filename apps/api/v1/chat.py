import logging
import json
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.chat.models import Conversation, Message
from apps.chat.serializers import ConversationSerializer, MessageSerializer


class ConversationView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        """
        GET /v1/chat/conversations
        List conversations for the logged-in user
        """
        qs = Conversation.objects.filter(participants=request.user).distinct()
        serializer = ConversationSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        """
        POST /v1/chat/conversations
        Create a new conversation
        Expected body: { "title": "Conversation title", "form": form_id, "instance": instance_id,"participants": [user_id1, user_id2] }
        """
        if request.data:
            data = request.data

            from apps.projects.models import FormData

            try:
                form_instance = FormData.objects.get(original_uuid=data["instance"])
            except FormData.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": f"FormData with uuid {data['instance']} not found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                # Create or update conversation object
                conversation, created = Conversation.objects.update_or_create(
                    form_id=data["form"],
                    instance_id=form_instance.id,
                    defaults={"title": data["title"], "created_by_id": request.user.id},
                )

                # Add current user + provided participants
                participant_list = [request.user.id] + data["participants"]
                conversation.participants.set(participant_list)
                conversation.save()

                return Response(
                    {
                        "success": True,
                        "message": "Conversation created successfully",
                        "data": ConversationSerializer(
                            conversation, context={"request": request}
                        ).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"success": False, "message": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        """
        GET  /v1/chat/conversations/<pk>/messages
        POST /v1/chat/conversations/<pk>/messages
        """
        try:
            conversation = Conversation.objects.get(pk=pk, participants=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=404)

        if request.method == "GET":
            msgs = conversation.messages.all().order_by("created_at")
            serializer = MessageSerializer(
                msgs, many=True, context={"request": request}
            )
            return Response(serializer.data)

        # POST – send message
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        external_id = serializer.validated_data.get("external_id")

        if not external_id:
            return Response(
                {"error": "external_id is required for idempotent messaging"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # insert or update message based on external id use update_or_insert method
        msg, created = Message.objects.update_or_create(
            external_id=external_id,
            defaults={
                "conversation": conversation,
                "sender": request.user,
                "text": serializer.validated_data["text"],
            },
        )

        return Response(
            {
                "success": True,
                "message": "Message created successfully",
                "data": MessageSerializer(msg, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """
        POST /v1/chat/conversations/<pk>/mark-read
        Marks all unread messages (not sent by current user) as read
        """
        try:
            conversation = Conversation.objects.get(pk=pk, participants=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=404)

        # mark all unread messages as read
        conversation.messages.filter(is_read=False).exclude(sender=request.user).update(
            is_read=True
        )

        # return success
        return Response(
            {
                "success": True,
                "message": "Conversation marked read successfully",
            }
        )
