from django.urls import path
from .views import TipCreateView, OfficerReviewView, DetectiveReviewView, RewardLookupView

urlpatterns = [
    path("tips/", TipCreateView.as_view(), name="tip-create"),
    path("tips/<int:id>/officer-review/", OfficerReviewView.as_view(), name="tip-officer-review"),
    path("tips/<int:id>/detective-review/", DetectiveReviewView.as_view(), name="tip-detective-review"),
    path("rewards/lookup/", RewardLookupView.as_view(), name="reward-lookup"),
]
