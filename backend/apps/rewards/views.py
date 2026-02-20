from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_BASE_USER, ROLE_POLICE_OFFICER, ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_SYSTEM_ADMIN
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.suspects.utils import compute_most_wanted
from .models import Tip, TipAttachment, RewardCode
from .serializers import TipSerializer, OfficerReviewSerializer, DetectiveReviewSerializer, RewardLookupSerializer


class TipCreateView(generics.ListCreateAPIView):
    serializer_class = TipSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_BASE_USER]

    def get_queryset(self):
        return Tip.objects.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        tip = serializer.save(submitted_by=self.request.user)
        for attachment in self.request.FILES.getlist("attachments"):
            TipAttachment.objects.create(tip=tip, file=attachment)
        return tip


class OfficerReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER]

    def post(self, request, id):
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

    def post(self, request, id):
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
            reward_code, _ = RewardCode.objects.get_or_create(
                tip=tip,
                user=tip.submitted_by,
                defaults={"code": RewardCode.generate_code()},
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
    required_roles = [ROLE_POLICE_OFFICER, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_SYSTEM_ADMIN]

    def get(self, request):
        serializer = RewardLookupSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        national_id = serializer.validated_data["national_id"]
        code = serializer.validated_data["code"]
        user = get_object_or_404(User, national_id=national_id)
        reward = get_object_or_404(RewardCode, code=code, user=user)
        reward_amount = 0
        if reward.tip.person:
            most_wanted = compute_most_wanted()
            for entry in most_wanted:
                if entry["person"].id == reward.tip.person.id:
                    reward_amount = entry["reward_amount"]
                    break
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
                "amount": reward_amount,
            },
        }
        return Response(data, status=status.HTTP_200_OK)
