from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_SYSTEM_ADMIN, ROLE_POLICE_CHIEF, ROLE_CAPTAIN, ROLE_POLICE_OFFICER
from .models import Person, SuspectCandidate, WantedRecord
from apps.notifications.models import Notification
from apps.cases.policies import can_user_access_case
from .serializers import (
    SuspectProposalSerializer,
    SuspectCandidateSerializer,
    SergeantDecisionSerializer,
    MostWantedSerializer,
    PersonSerializer,
    SuspectStatusUpdateSerializer,
)
from .utils import compute_most_wanted
from apps.cases.models import Case


class SuspectProposalView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_DETECTIVE]

    @extend_schema(request=SuspectProposalSerializer, responses={201: SuspectCandidateSerializer(many=True)})
    def post(self, request, case_id):
        """Submit one or more suspect candidates for a case together with the detective rationale."""

        case = get_object_or_404(Case, id=case_id)
        from apps.cases.models import CaseAssignment
        if not CaseAssignment.objects.filter(case=case, user=request.user, role_in_case="detective").exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SuspectProposalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = []
        for person_data in serializer.validated_data["suspects"]:
            person_id = person_data.pop("id", None)
            if person_id:
                person = get_object_or_404(Person, id=person_id)
            else:
                person = Person.objects.create(**person_data)
            candidate = SuspectCandidate.objects.create(
                case=case,
                person=person,
                proposed_by_detective=request.user,
                rationale=serializer.validated_data["rationale"],
            )
            created.append(candidate)
        return Response(SuspectCandidateSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class SergeantDecisionView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT]

    @extend_schema(request=SergeantDecisionSerializer, responses={200: SuspectCandidateSerializer})
    def post(self, request, case_id, suspect_id):
        """Approve or reject a suspect candidate and notify the proposing detective."""

        candidate = get_object_or_404(SuspectCandidate, id=suspect_id, case_id=case_id)
        if not can_user_access_case(request.user, candidate.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SergeantDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        message = serializer.validated_data.get("message", "")
        if approve:
            candidate.status = "approved"
            WantedRecord.objects.get_or_create(person=candidate.person, case=candidate.case)
        else:
            candidate.status = "rejected"
        candidate.sergeant_message = message
        candidate.decided_at = timezone.now()
        candidate.save()
        if candidate.proposed_by_detective_id:
            Notification.objects.create(
                user=candidate.proposed_by_detective,
                case=candidate.case,
                type="suspect_decision",
                payload={
                    "candidate_id": candidate.id,
                    "status": candidate.status,
                    "message": message,
                },
            )
        return Response(SuspectCandidateSerializer(candidate).data, status=status.HTTP_200_OK)


class MostWantedPublicView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: MostWantedSerializer(many=True)})
    def get(self, request):
        """Return the public most-wanted ranking visible to all users."""

        results = compute_most_wanted()
        serializer = MostWantedSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MostWantedPoliceView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]

    @extend_schema(request=None, responses={200: MostWantedSerializer(many=True)})
    def get(self, request):
        """Return the police-facing most-wanted ranking for authorized staff."""

        results = compute_most_wanted()
        serializer = MostWantedSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuspectStatusUpdateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]

    @extend_schema(request=SuspectStatusUpdateSerializer, responses={200: PersonSerializer})
    def post(self, request, person_id):
        """Update a suspect's status within a case, such as wanted, arrested, or cleared."""

        person = get_object_or_404(Person, id=person_id)
        serializer = SuspectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_value = serializer.validated_data["status"]
        case_id = serializer.validated_data["case_id"]
        case = get_object_or_404(Case, id=case_id)
        record = WantedRecord.objects.filter(person=person, case=case).first() if case else None
        if not record and case:
            record = WantedRecord.objects.create(person=person, case=case)
        if record:
            record.status = status_value
            if status_value in ["arrested", "cleared"]:
                record.ended_at = timezone.now()
            record.save()
        return Response(PersonSerializer(person).data, status=status.HTTP_200_OK)
