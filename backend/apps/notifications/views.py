from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationReadView(APIView):
    def post(self, request, id):
        notification = Notification.objects.filter(id=id, user=request.user).first()
        if not notification:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notification.read_at = timezone.now()
        notification.save()
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)
