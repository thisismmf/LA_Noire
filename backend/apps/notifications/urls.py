from django.urls import path
from .views import NotificationListView, NotificationReadView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:id>/read/", NotificationReadView.as_view(), name="notification-read"),
]
