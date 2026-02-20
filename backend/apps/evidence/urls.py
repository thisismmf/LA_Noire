from django.urls import path
from .views import EvidenceListCreateView, EvidenceDetailView

urlpatterns = [
    path("cases/<int:case_id>/evidence/", EvidenceListCreateView.as_view(), name="case-evidence"),
    path("evidence/<int:id>/", EvidenceDetailView.as_view(), name="evidence-detail"),
]
