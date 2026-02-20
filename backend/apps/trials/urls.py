from django.urls import path
from .views import CaseReportView, TrialDecisionView

urlpatterns = [
    path("cases/<int:case_id>/report/", CaseReportView.as_view(), name="case-report"),
    path("cases/<int:case_id>/trial/decision/", TrialDecisionView.as_view(), name="trial-decision"),
]
