from django.urls import path
from .views import (
    InterrogationCreateView,
    DetectiveScoreView,
    SergeantScoreView,
    CaptainDecisionView,
    ChiefDecisionView,
)

urlpatterns = [
    path("cases/<int:case_id>/interrogations/", InterrogationCreateView.as_view(), name="interrogation-create"),
    path("interrogations/<int:id>/detective-score/", DetectiveScoreView.as_view(), name="interrogation-detective-score"),
    path("interrogations/<int:id>/sergeant-score/", SergeantScoreView.as_view(), name="interrogation-sergeant-score"),
    path("interrogations/<int:id>/captain-decision/", CaptainDecisionView.as_view(), name="interrogation-captain-decision"),
    path("interrogations/<int:id>/chief-decision/", ChiefDecisionView.as_view(), name="interrogation-chief-decision"),
]
