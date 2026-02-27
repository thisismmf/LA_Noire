from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF
from apps.cases.models import Case
from apps.cases.constants import CrimeLevel, CaseStatus
from apps.cases.policies import is_user_assigned_to_case
from apps.suspects.models import Person
from apps.notifications.models import Notification
from .models import Interrogation
from .serializers import (
    InterrogationSerializer,
    InterrogationCreateSerializer,
    ScoreSerializer,
    CaptainDecisionSerializer,
    ChiefDecisionSerializer,
)


class InterrogationCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_DETECTIVE]

    @extend_schema(request=InterrogationCreateSerializer, responses={201: InterrogationSerializer})
    def post(self, request, case_id):
        """Create an interrogation record for a suspect in a case assigned to the requesting detective."""

        case = get_object_or_404(Case, id=case_id)
        from apps.cases.models import CaseAssignment
        if not CaseAssignment.objects.filter(case=case, user=request.user, role_in_case="detective").exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = InterrogationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suspect = get_object_or_404(Person, id=serializer.validated_data["suspect_id"])
        interrogation = Interrogation.objects.create(
            case=case,
            suspect=suspect,
            detective_score=serializer.validated_data.get("detective_score"),
            status="pending_sergeant",
        )
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_201_CREATED)


class DetectiveScoreView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_DETECTIVE]

    @extend_schema(request=ScoreSerializer, responses={200: InterrogationSerializer})
    def patch(self, request, id):
        """Record or revise the detective guilt score for an interrogation awaiting detective input."""

        interrogation = get_object_or_404(Interrogation, id=id)
        if not is_user_assigned_to_case(request.user, interrogation.case, role_in_case="detective"):
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if interrogation.status not in ["pending_detective", "pending_sergeant"]:
            return Response(
                {"error": {"code": "invalid_state", "message": "Not awaiting detective score", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ScoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interrogation.detective_score = serializer.validated_data["score"]
        if interrogation.status == "pending_detective":
            interrogation.status = "pending_sergeant"
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)


class SergeantScoreView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT]

    @extend_schema(request=ScoreSerializer, responses={200: InterrogationSerializer})
    def patch(self, request, id):
        """Record the sergeant guilt score and advance the interrogation to captain review."""

        interrogation = get_object_or_404(Interrogation, id=id)
        if not is_user_assigned_to_case(request.user, interrogation.case, role_in_case="sergeant"):
            return Response(
                {"error": {"code": "forbidden", "message": "Sergeant not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if interrogation.status != "pending_sergeant":
            return Response(
                {"error": {"code": "invalid_state", "message": "Not awaiting sergeant score", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ScoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interrogation.sergeant_score = serializer.validated_data["score"]
        interrogation.status = "pending_captain"
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)


class CaptainDecisionView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CAPTAIN]

    @extend_schema(request=CaptainDecisionSerializer, responses={200: InterrogationSerializer})
    def post(self, request, id):
        """Record the captain decision and escalate critical cases to chief approval when required."""

        interrogation = get_object_or_404(Interrogation, id=id)
        if interrogation.case.status not in [CaseStatus.ACTIVE, CaseStatus.CLOSED_SOLVED, CaseStatus.CLOSED_UNSOLVED]:
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if interrogation.status != "pending_captain":
            return Response(
                {"error": {"code": "invalid_state", "message": "Not awaiting captain decision", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CaptainDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        if decision == "approve" and Interrogation.objects.filter(
            case=interrogation.case,
            status="approved",
        ).exclude(id=interrogation.id).exists():
            return Response(
                {"error": {"code": "invalid_state", "message": "An offender is already approved for this case", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        interrogation.captain_decision = serializer.validated_data["decision"]
        interrogation.captain_notes = serializer.validated_data.get("notes", "")
        interrogation.captain_reviewed_by = request.user
        if interrogation.case.crime_level == CrimeLevel.CRITICAL:
            interrogation.status = "pending_chief"
        else:
            interrogation.status = "approved" if decision == "approve" else "rejected"
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)


class ChiefDecisionView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_CHIEF]

    @extend_schema(request=ChiefDecisionSerializer, responses={200: InterrogationSerializer})
    def post(self, request, id):
        """Record the chief of police decision for a critical-crime interrogation."""

        interrogation = get_object_or_404(Interrogation, id=id)
        if interrogation.case.status not in [CaseStatus.ACTIVE, CaseStatus.CLOSED_SOLVED, CaseStatus.CLOSED_UNSOLVED]:
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if interrogation.status != "pending_chief":
            return Response(
                {"error": {"code": "invalid_state", "message": "Not awaiting chief decision", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ChiefDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        if decision == "approve" and Interrogation.objects.filter(
            case=interrogation.case,
            status="approved",
        ).exclude(id=interrogation.id).exists():
            return Response(
                {"error": {"code": "invalid_state", "message": "An offender is already approved for this case", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        interrogation.chief_decision = decision
        interrogation.chief_notes = serializer.validated_data.get("notes", "")
        if decision == "approve":
            interrogation.status = "approved"
        else:
            interrogation.status = "pending_captain"
            if interrogation.captain_reviewed_by_id:
                Notification.objects.create(
                    user=interrogation.captain_reviewed_by,
                    case=interrogation.case,
                    type="chief_rejected_interrogation_decision",
                    payload={
                        "interrogation_id": interrogation.id,
                        "chief_notes": interrogation.chief_notes,
                    },
                )
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)
