from django.urls import path
from .views import SuspectProposalView, SergeantDecisionView, MostWantedPublicView, MostWantedPoliceView, SuspectStatusUpdateView

urlpatterns = [
    path("cases/<int:case_id>/suspects/propose/", SuspectProposalView.as_view(), name="suspect-propose"),
    path("cases/<int:case_id>/suspects/<int:suspect_id>/sergeant-decision/", SergeantDecisionView.as_view(), name="suspect-sergeant-decision"),
    path("suspects/most-wanted/", MostWantedPoliceView.as_view(), name="most-wanted-police"),
    path("public/most-wanted/", MostWantedPublicView.as_view(), name="most-wanted-public"),
    path("suspects/<int:person_id>/status/", SuspectStatusUpdateView.as_view(), name="suspect-status"),
]
