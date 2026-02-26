from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """List notifications for the authenticated user in reverse chronological order."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationReadView(APIView):
    @extend_schema(request=None, responses={200: NotificationSerializer, 404: None})
    def post(self, request, id):
        """Mark a user-owned notification as read and return the updated notification."""

        notification = Notification.objects.filter(id=id, user=request.user).first()
        if not notification:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notification.read_at = timezone.now()
        notification.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)
