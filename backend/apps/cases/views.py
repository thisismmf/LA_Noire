from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import (
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_SYSTEM_ADMIN,
    ROLE_COMPLAINANT,
    ROLE_BASE_USER,
)
from apps.rbac.utils import user_has_role, get_role_by_slug
from .models import Complaint, Case, CaseComplainant, CaseReview, CrimeSceneReport, CaseAssignment
from .serializers import (
    ComplaintSerializer,
    ComplaintResubmitSerializer,
    CadetReviewSerializer,
    OfficerReviewSerializer,
    CrimeSceneReportSerializer,
    CrimeSceneApproveSerializer,
    CaseSerializer,
    AddComplainantSerializer,
)
from .constants import ComplaintStatus, CaseStatus, CrimeSceneStatus, CaseSourceType
from .policies import get_required_approver_role_slug, POLICE_ROLES


class ComplaintCreateView(generics.CreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_COMPLAINANT, ROLE_BASE_USER]

    def perform_create(self, serializer):
        complaint = serializer.save(created_by=self.request.user)
        if not user_has_role(self.request.user, [ROLE_COMPLAINANT]):
            role = get_role_by_slug(ROLE_COMPLAINANT)
            if role:
                self.request.user.user_roles.get_or_create(role=role)
        return complaint


class ComplaintDetailView(generics.RetrieveAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        user = self.request.user
        if user_has_role(user, [ROLE_SYSTEM_ADMIN, ROLE_CADET, ROLE_POLICE_OFFICER]):
            return Complaint.objects.all()
        return Complaint.objects.filter(created_by=user)


class ComplaintResubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ComplaintResubmitSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        complaint = get_object_or_404(Complaint, id=id, created_by=request.user)
        if complaint.status != ComplaintStatus.RETURNED_TO_COMPLAINANT:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not returned to complainant", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ComplaintResubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint.strike_count += 1
        if complaint.strike_count >= 3:
            complaint.status = ComplaintStatus.VOIDED
            complaint.save()
            return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)
        for field, value in serializer.validated_data.items():
            setattr(complaint, field, value)
        complaint.status = ComplaintStatus.PENDING_CADET_REVIEW
        complaint.last_message = ""
        complaint.save()
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class CadetReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CADET]

    @extend_schema(request=CadetReviewSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        complaint = get_object_or_404(Complaint, id=id)
        if complaint.status not in [ComplaintStatus.PENDING_CADET_REVIEW, ComplaintStatus.RETURNED_TO_CADET]:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not in cadet review", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CadetReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        message = serializer.validated_data.get("message", "")
        if action == "return":
            complaint.status = ComplaintStatus.RETURNED_TO_COMPLAINANT
            complaint.last_message = message
        else:
            complaint.status = ComplaintStatus.PENDING_OFFICER_REVIEW
        complaint.save()
        CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class OfficerReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER]

    @extend_schema(request=OfficerReviewSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        complaint = get_object_or_404(Complaint, id=id)
        if complaint.status != ComplaintStatus.PENDING_OFFICER_REVIEW:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not in officer review", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = OfficerReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        message = serializer.validated_data.get("message", "")
        if action == "return_to_cadet":
            complaint.status = ComplaintStatus.RETURNED_TO_CADET
            complaint.last_message = message
            complaint.save()
            CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
            return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)
        complaint.status = ComplaintStatus.APPROVED
        complaint.last_message = ""
        complaint.save()
        case = Case.objects.create(
            title=complaint.title,
            description=complaint.description,
            crime_level=complaint.crime_level,
            location=complaint.location,
            incident_datetime=complaint.incident_datetime,
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=request.user,
            complaint=complaint,
        )
        CaseComplainant.objects.filter(complaint=complaint).update(case=case, is_verified=True)
        CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class CrimeSceneCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER, ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF]

    @extend_schema(request=CrimeSceneReportSerializer, responses={201: CaseSerializer})
    def post(self, request):
        serializer = CrimeSceneReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        required_role_slug = get_required_approver_role_slug(request.user)
        case_status = CaseStatus.ACTIVE if required_role_slug is None else CaseStatus.PENDING_SUPERIOR_APPROVAL
        case = Case.objects.create(
            title=serializer.validated_data["title"],
            description=serializer.validated_data["description"],
            crime_level=serializer.validated_data["crime_level"],
            location=serializer.validated_data["location"],
            incident_datetime=serializer.validated_data.get("incident_datetime"),
            status=case_status,
            source_type=CaseSourceType.CRIME_SCENE,
            created_by=request.user,
        )
        required_role = get_role_by_slug(required_role_slug) if required_role_slug else None
        report = CrimeSceneReport.objects.create(
            case=case,
            reported_by=request.user,
            scene_datetime=serializer.validated_data["scene_datetime"],
            status=CrimeSceneStatus.APPROVED if required_role_slug is None else CrimeSceneStatus.PENDING_APPROVAL,
            required_approver_role=required_role,
        )
        for witness in serializer.validated_data["witnesses"]:
            report.witnesses.create(**witness)
        return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)


class CrimeSceneApproveView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF]

    @extend_schema(request=CrimeSceneApproveSerializer, responses={200: CaseSerializer})
    def post(self, request, id):
        report = get_object_or_404(CrimeSceneReport, id=id)
        if report.status != CrimeSceneStatus.PENDING_APPROVAL:
            return Response(
                {"error": {"code": "invalid_state", "message": "Report not pending approval", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CrimeSceneApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        required_role = report.required_approver_role
        if required_role and not user_has_role(request.user, [required_role.slug]):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized to approve", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if approve:
            report.status = CrimeSceneStatus.APPROVED
            report.approved_by = request.user
            report.approved_at = timezone.now()
            report.case.status = CaseStatus.ACTIVE
            report.case.save()
        else:
            report.status = CrimeSceneStatus.REJECTED
            report.case.status = CaseStatus.VOIDED
            report.case.save()
        report.save()
        return Response(CaseSerializer(report.case).data, status=status.HTTP_200_OK)


class CaseListView(generics.ListAPIView):
    serializer_class = CaseSerializer

    def get_queryset(self):
        user = self.request.user
        if user_has_role(user, [ROLE_SYSTEM_ADMIN]):
            return Case.objects.all()
        assigned_case_ids = CaseAssignment.objects.filter(user=user).values_list("case_id", flat=True)
        complaint_case_ids = Case.objects.filter(complaint__created_by=user).values_list("id", flat=True)
        created_case_ids = Case.objects.filter(created_by=user).values_list("id", flat=True)
        return Case.objects.filter(id__in=list(assigned_case_ids) + list(complaint_case_ids) + list(created_case_ids))


class CaseDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CaseSerializer

    def get_queryset(self):
        user = self.request.user
        if user_has_role(user, [ROLE_SYSTEM_ADMIN]):
            return Case.objects.all()
        assigned_case_ids = CaseAssignment.objects.filter(user=user).values_list("case_id", flat=True)
        complaint_case_ids = Case.objects.filter(complaint__created_by=user).values_list("id", flat=True)
        created_case_ids = Case.objects.filter(created_by=user).values_list("id", flat=True)
        return Case.objects.filter(id__in=list(assigned_case_ids) + list(complaint_case_ids) + list(created_case_ids))

    def update(self, request, *args, **kwargs):
        if not user_has_role(request.user, list(POLICE_ROLES)):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if "status" in request.data:
            case = self.get_object()
            current = case.status
            desired = request.data.get("status")
            allowed = {
                CaseStatus.PENDING_SUPERIOR_APPROVAL: [CaseStatus.ACTIVE, CaseStatus.VOIDED],
                CaseStatus.ACTIVE: [CaseStatus.CLOSED_SOLVED, CaseStatus.CLOSED_UNSOLVED, CaseStatus.VOIDED],
            }
            if current != desired and desired not in allowed.get(current, []):
                return Response(
                    {"error": {"code": "invalid_state", "message": "Invalid case status transition", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().update(request, *args, **kwargs)


class AddComplainantView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CADET]

    @extend_schema(request=AddComplainantSerializer, responses={200: CaseSerializer})
    def post(self, request, id):
        case = get_object_or_404(Case, id=id)
        serializer = AddComplainantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CaseComplainant.objects.create(case=case, **serializer.validated_data, is_verified=True)
        return Response(CaseSerializer(case).data, status=status.HTTP_200_OK)
