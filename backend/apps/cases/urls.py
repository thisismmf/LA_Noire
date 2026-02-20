from django.urls import path
from .views import (
    ComplaintCreateView,
    ComplaintDetailView,
    ComplaintResubmitView,
    CadetReviewView,
    OfficerReviewView,
    CrimeSceneCreateView,
    CrimeSceneApproveView,
    CaseListView,
    CaseDetailView,
    AddComplainantView,
)

urlpatterns = [
    path("cases/complaints/", ComplaintCreateView.as_view(), name="complaint-create"),
    path("cases/complaints/<int:id>/", ComplaintDetailView.as_view(), name="complaint-detail"),
    path("cases/complaints/<int:id>/resubmit/", ComplaintResubmitView.as_view(), name="complaint-resubmit"),
    path("cases/complaints/<int:id>/cadet-review/", CadetReviewView.as_view(), name="complaint-cadet-review"),
    path("cases/complaints/<int:id>/officer-review/", OfficerReviewView.as_view(), name="complaint-officer-review"),
    path("cases/crime-scene/", CrimeSceneCreateView.as_view(), name="crime-scene-create"),
    path("cases/crime-scene/<int:id>/approve/", CrimeSceneApproveView.as_view(), name="crime-scene-approve"),
    path("cases/", CaseListView.as_view(), name="case-list"),
    path("cases/<int:pk>/", CaseDetailView.as_view(), name="case-detail"),
    path("cases/<int:id>/add-complainant/", AddComplainantView.as_view(), name="case-add-complainant"),
]
