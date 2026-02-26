from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import (
    ROLE_BASE_USER,
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
)
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.suspects.utils import compute_most_wanted
from .models import Tip, TipAttachment, RewardCode
from .serializers import (
    TipSerializer,
    OfficerReviewSerializer,
    DetectiveReviewSerializer,
    RewardLookupSerializer,
    RewardLookupResponseSerializer,
)


def _compute_tip_reward_amount(tip):
    if not tip.person_id:
        return 0
    most_wanted = compute_most_wanted()
    for entry in most_wanted:
        if entry["person"].id == tip.person_id:
            return entry["reward_amount"]
    return 0


class TipCreateView(generics.ListCreateAPIView):
    """List tips submitted by the current base user and allow them to submit a new tip with optional attachments."""

    serializer_class = TipSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_BASE_USER]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tip.objects.none()
        return Tip.objects.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        tip = serializer.save(submitted_by=self.request.user)
        for attachment in self.request.FILES.getlist("attachments"):
            TipAttachment.objects.create(tip=tip, file=attachment)
        return tip


class TipReviewQueueView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_DETECTIVE, ROLE_SYSTEM_ADMIN]

    @extend_schema(request=None, responses={200: TipSerializer(many=True)})
    def get(self, request):
        """Return the appropriate tip review queue for police officers, detectives, or system administrators."""

        role_slugs = set(request.user.user_roles.values_list("role__slug", flat=True))
        if ROLE_SYSTEM_ADMIN in role_slugs:
            queryset = Tip.objects.all()
        elif ROLE_POLICE_OFFICER in role_slugs:
            queryset = Tip.objects.filter(status="pending_officer")
        else:
            queryset = Tip.objects.filter(status="pending_detective").filter(
                Q(case__isnull=True) | Q(case__assignments__user=request.user, case__assignments__role_in_case="detective")
            )
        queryset = queryset.order_by("-created_at").distinct()
        return Response(TipSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class OfficerReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER]

    @extend_schema(request=OfficerReviewSerializer, responses={200: TipSerializer})
    def post(self, request, id):
        """Perform the first-stage police review for a submitted tip."""

        tip = get_object_or_404(Tip, id=id)
        serializer = OfficerReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        tip.officer_reviewer = request.user
        if approve:
            tip.status = "pending_detective"
        else:
            tip.status = "rejected"
            tip.decided_at = timezone.now()
        tip.save()
        return Response(TipSerializer(tip).data, status=status.HTTP_200_OK)


class DetectiveReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_DETECTIVE]

    @extend_schema(request=DetectiveReviewSerializer, responses={200: TipSerializer})
    def post(self, request, id):
        """Perform the detective review, issue a reward code on acceptance, and notify the submitting user."""

        tip = get_object_or_404(Tip, id=id)
        if tip.case:
            from apps.cases.models import CaseAssignment
            if not CaseAssignment.objects.filter(case=tip.case, user=request.user, role_in_case="detective").exists():
                return Response(
                    {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer = DetectiveReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        tip.detective_reviewer = request.user
        if approve:
            tip.status = "accepted"
            tip.decided_at = timezone.now()
            reward_amount = _compute_tip_reward_amount(tip)
            reward_code, _ = RewardCode.objects.get_or_create(
                tip=tip,
                user=tip.submitted_by,
                defaults={"code": RewardCode.generate_code(), "amount": reward_amount},
            )
            Notification.objects.create(
                user=tip.submitted_by,
                case=tip.case,
                type="reward_issued",
                payload={"code": reward_code.code},
            )
        else:
            tip.status = "rejected"
            tip.decided_at = timezone.now()
        tip.save()
        return Response(TipSerializer(tip).data, status=status.HTTP_200_OK)


class RewardLookupView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [
        ROLE_CADET,
        ROLE_POLICE_OFFICER,
        ROLE_PATROL_OFFICER,
        ROLE_DETECTIVE,
        ROLE_SERGEANT,
        ROLE_CAPTAIN,
        ROLE_POLICE_CHIEF,
        ROLE_CORONER,
        ROLE_SYSTEM_ADMIN,
    ]

    @extend_schema(request=None, responses={200: RewardLookupResponseSerializer})
    def get(self, request):
        """Look up an issued reward by national ID and reward code for in-person payout verification."""

        serializer = RewardLookupSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        national_id = serializer.validated_data["national_id"]
        code = serializer.validated_data["code"]
        user = get_object_or_404(User, national_id=national_id)
        reward = get_object_or_404(RewardCode, code=code, user=user)
        data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "national_id": user.national_id,
            },
            "tip": {
                "id": reward.tip.id,
                "content": reward.tip.content,
                "status": reward.tip.status,
            },
            "reward": {
                "code": reward.code,
                "issued_at": reward.issued_at,
                "redeemed_at": reward.redeemed_at,
                "status": "redeemed" if reward.redeemed_at else "issued",
                "amount": reward.amount,
            },
        }
        return Response(data, status=status.HTTP_200_OK)
