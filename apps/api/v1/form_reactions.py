import datetime

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.ohkr.models import FormReaction
from apps.ohkr.serializers import FormReactionSerializer

class FormReactionView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    """
    API for downloading Form Logic Reactions (Decision Trees)
    to the mobile app.
    """

    def list(self, request):
        """
        Get all active reactions. 
        Optionally filter by form_id via query params.
        """
        queryset = FormReaction.objects.filter(is_active=True)
        
        form_id = request.query_params.get('form_id')
        if form_id:
            queryset = queryset.filter(form_id=form_id)

        # Prefetch related actions to optimize database hits (select_related/prefetch_related)
        queryset = queryset.prefetch_related('actions').order_by('priority')
        
        serializer = FormReactionSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Get reactions for a specific form_id"""
        try:
            # We use form_id as the lookup instead of the DB primary key for app convenience
            reactions = FormReaction.objects.filter(
                form_id=pk, 
                is_active=True
            ).prefetch_related('actions').order_by('priority')
            
            serializer = FormReactionSerializer(reactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": True, "message": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    def sync(self, request):
        """
        Bulk sync endpoint: returns rules updated after a certain timestamp
        to minimize data transfer.
        """
        last_sync = request.data.get("last_sync")
        queryset = FormReaction.objects.filter(is_active=True)
        
        if last_sync:
            queryset = queryset.filter(updated_at__gt=last_sync)
            
        serializer = FormReactionSerializer(queryset, many=True)
        return Response({
            "error": False,
            "server_time": datetime.now(),
            "reactions": serializer.data
        }, status=status.HTTP_200_OK)