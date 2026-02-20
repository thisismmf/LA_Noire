from django.urls import path
from .views import StatsOverviewView

urlpatterns = [
    path("stats/overview/", StatsOverviewView.as_view(), name="stats-overview"),
]
