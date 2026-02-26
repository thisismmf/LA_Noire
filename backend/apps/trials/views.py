from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_JUDGE, ROLE_CAPTAIN, ROLE_POLICE_CHIEF
from apps.cases.models import Case
from apps.cases.policies import can_user_access_case
from apps.cases.serializers import CaseSerializer
from apps.cases.models import CaseReview, CrimeSceneReport, CaseAssignment
from apps.evidence.models import Evidence
from apps.evidence.serializers import EvidenceSerializer
from apps.suspects.models import SuspectCandidate
from apps.suspects.serializers import SuspectCandidateSerializer
from apps.interrogations.models import Interrogation
from apps.interrogations.serializers import InterrogationSerializer
from apps.rbac.utils import get_user_role_slugs
from .models import Trial
from .serializers import TrialSerializer, TrialDecisionSerializer, CaseReportResponseSerializer


class CaseReportView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_JUDGE, ROLE_CAPTAIN, ROLE_POLICE_CHIEF]

    @extend_schema(request=None, responses={200: CaseReportResponseSerializer})
    def get(self, request, case_id):
        """Return the complete judge-facing case report with evidence, assignments, reviews, and interrogation history."""

        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        evidence = Evidence.objects.filter(case=case)
        suspects = SuspectCandidate.objects.filter(case=case)
        interrogations = Interrogation.objects.filter(case=case)
        assignments = CaseAssignment.objects.filter(case=case)
        reviews = CaseReview.objects.filter(complaint=case.complaint) if case.complaint else []
        crime_scene = CrimeSceneReport.objects.filter(case=case).first()
        data = {
            "case": CaseSerializer(case).data,
            "complaint": {
                "id": case.complaint.id,
                "status": case.complaint.status,
                "strike_count": case.complaint.strike_count,
                "last_message": case.complaint.last_message,
            } if case.complaint else None,
            "crime_scene_report": {
                "id": crime_scene.id,
                "status": crime_scene.status,
                "scene_datetime": crime_scene.scene_datetime,
                "reported_by": crime_scene.reported_by_id,
                "approved_by": crime_scene.approved_by_id,
                "approved_at": crime_scene.approved_at,
                "witnesses": [
                    {
                        "full_name": w.full_name,
                        "phone": w.phone,
                        "national_id": w.national_id,
                    }
                    for w in crime_scene.witnesses.all()
                ],
            } if crime_scene else None,
            "reviews": [
                {"decision": r.decision, "message": r.message, "reviewer": r.reviewer_id, "created_at": r.created_at}
                for r in reviews
            ],
            "evidence": EvidenceSerializer(evidence, many=True).data,
            "suspects": SuspectCandidateSerializer(suspects, many=True).data,
            "interrogations": InterrogationSerializer(interrogations, many=True).data,
            "assignments": [
                {
                    "user": {
                        "id": a.user_id,
                        "username": a.user.username,
                        "first_name": a.user.first_name,
                        "last_name": a.user.last_name,
                        "national_id": a.user.national_id,
                        "roles": get_user_role_slugs(a.user),
                    },
                    "role_in_case": a.role_in_case,
                    "assigned_at": a.assigned_at,
                }
                for a in assignments
            ],
        }
        return Response(data, status=status.HTTP_200_OK)


class TrialDecisionView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_JUDGE]

    @extend_schema(request=TrialDecisionSerializer, responses={200: TrialSerializer})
    def post(self, request, case_id):
        """Record the judge's final verdict and punishment details for a case."""

        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TrialDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trial, _ = Trial.objects.update_or_create(
            case=case,
            defaults={
                "judge": request.user,
                "verdict": serializer.validated_data["verdict"],
                "punishment_title": serializer.validated_data.get("punishment_title", ""),
                "punishment_description": serializer.validated_data.get("punishment_description", ""),
            },
        )
        return Response(TrialSerializer(trial).data, status=status.HTTP_200_OK)
