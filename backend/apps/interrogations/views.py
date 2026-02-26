from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF
from apps.cases.models import Case
from apps.cases.constants import CrimeLevel
from apps.cases.policies import can_user_access_case, is_user_assigned_to_case
from apps.suspects.models import Person
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
        interrogation = get_object_or_404(Interrogation, id=id)
        if not can_user_access_case(request.user, interrogation.case):
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
        interrogation.captain_decision = serializer.validated_data["decision"]
        interrogation.captain_notes = serializer.validated_data.get("notes", "")
        if interrogation.case.crime_level == CrimeLevel.CRITICAL:
            interrogation.status = "pending_chief"
        else:
            interrogation.status = "approved" if serializer.validated_data["decision"] == "approve" else "rejected"
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)


class ChiefDecisionView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_CHIEF]

    @extend_schema(request=ChiefDecisionSerializer, responses={200: InterrogationSerializer})
    def post(self, request, id):
        interrogation = get_object_or_404(Interrogation, id=id)
        if not can_user_access_case(request.user, interrogation.case):
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
        interrogation.chief_decision = serializer.validated_data["decision"]
        interrogation.chief_notes = serializer.validated_data.get("notes", "")
        interrogation.status = "approved" if serializer.validated_data["decision"] == "approve" else "rejected"
        interrogation.save()
        return Response(InterrogationSerializer(interrogation).data, status=status.HTTP_200_OK)
