from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import (
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
    ROLE_COMPLAINANT,
    ROLE_BASE_USER,
)
from apps.rbac.utils import user_has_role, get_role_by_slug
from apps.accounts.models import User
from apps.notifications.models import Notification
from .models import Complaint, Case, CaseComplainant, CaseReview, CrimeSceneReport, CaseAssignment
from .serializers import (
    ComplaintSerializer,
    ComplaintResubmitSerializer,
    CadetReviewSerializer,
    OfficerReviewSerializer,
    CrimeSceneReportSerializer,
    CrimeSceneApproveSerializer,
    CrimeSceneActionResponseSerializer,
    CaseSerializer,
    AddComplainantSerializer,
    ComplainantReviewSerializer,
    CaseComplainantSerializer,
    CaseAssignmentSerializer,
    CaseAssignmentUpsertSerializer,
)
from .constants import ComplaintStatus, CaseStatus, CrimeSceneStatus, CaseSourceType, CaseAssignmentRole
from .policies import get_required_approver_role_slug, POLICE_ROLES, can_user_access_case, get_primary_role, ROLE_PRIORITY


POLICE_VISIBILITY_ROLES = {
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
}

NON_CADET_POLICE_VISIBILITY_ROLES = POLICE_VISIBILITY_ROLES - {ROLE_CADET}

WORKFLOW_VISIBLE_CASE_STATUSES = [
    CaseStatus.ACTIVE,
    CaseStatus.CLOSED_SOLVED,
    CaseStatus.CLOSED_UNSOLVED,
    CaseStatus.VOIDED,
]


def _is_superior_role(viewer_role, creator_role):
    if not viewer_role or not creator_role:
        return False
    role_rank = {role: index for index, role in enumerate(ROLE_PRIORITY)}
    viewer_rank = role_rank.get(viewer_role)
    creator_rank = role_rank.get(creator_role)
    if viewer_rank is None or creator_rank is None:
        return False
    return viewer_rank < creator_rank


def _case_queryset_for_user(user):
    if not user or not user.is_authenticated:
        return Case.objects.none()
    if user_has_role(user, [ROLE_SYSTEM_ADMIN]):
        return Case.objects.all()
    queryset = Case.objects.filter(
        Q(assignments__user=user) | Q(complaint__created_by=user) | Q(created_by=user)
    )
    user_role_slugs = set(user.user_roles.select_related("role").values_list("role__slug", flat=True))
    if user_role_slugs & POLICE_VISIBILITY_ROLES:
        queryset = queryset | Case.objects.filter(
            source_type=CaseSourceType.COMPLAINT,
            status__in=WORKFLOW_VISIBLE_CASE_STATUSES,
        )
        if user_role_slugs & NON_CADET_POLICE_VISIBILITY_ROLES:
            queryset = queryset | Case.objects.filter(
                source_type=CaseSourceType.CRIME_SCENE,
                status__in=WORKFLOW_VISIBLE_CASE_STATUSES,
            )
    viewer_primary_role = get_primary_role(user)
    if viewer_primary_role in ROLE_PRIORITY:
        pending_crime_scene_cases = Case.objects.filter(
            source_type=CaseSourceType.CRIME_SCENE,
            status=CaseStatus.PENDING_SUPERIOR_APPROVAL,
        ).exclude(created_by=user).select_related("created_by")
        superior_visible_case_ids = []
        for case in pending_crime_scene_cases:
            creator_primary_role = get_primary_role(case.created_by)
            if _is_superior_role(viewer_primary_role, creator_primary_role):
                superior_visible_case_ids.append(case.id)
        if superior_visible_case_ids:
            queryset = queryset | Case.objects.filter(id__in=superior_visible_case_ids)
    return queryset.distinct()


class ComplaintCreateView(generics.CreateAPIView):
    """Submit a new complaint that enters the cadet and police review workflow for case formation."""

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
    """Retrieve a complaint visible to the current user or reviewing police staff."""

    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        user = self.request.user
        if user_has_role(user, [ROLE_SYSTEM_ADMIN]):
            return Complaint.objects.all()
        queryset = Complaint.objects.filter(created_by=user)
        if user_has_role(user, [ROLE_CADET]):
            queryset = queryset | Complaint.objects.filter(
                Q(assigned_cadet=user) | Q(status=ComplaintStatus.PENDING_CADET_REVIEW, assigned_cadet__isnull=True)
            )
        if user_has_role(user, [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER]):
            queryset = queryset | Complaint.objects.filter(
                status=ComplaintStatus.PENDING_OFFICER_REVIEW,
                assigned_officer=user,
            )
        return queryset.distinct()


class ComplaintQueueView(generics.ListAPIView):
    """List complaint review queues according to the requesting user's role and optional filters."""

    serializer_class = ComplaintSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CADET, ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER, ROLE_SYSTEM_ADMIN]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(name="status", type=str, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name="ordering",
                type=str,
                required=False,
                location=OpenApiParameter.QUERY,
                description="Use `created_at` or `-created_at`",
            ),
        ],
        responses={200: ComplaintSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        """Return the complaint queue for cadets, officers, or system administrators."""

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering not in ("created_at", "-created_at"):
            ordering = "-created_at"
        status_filter = self.request.query_params.get("status")
        if user_has_role(user, [ROLE_SYSTEM_ADMIN]):
            queryset = Complaint.objects.all()
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            return queryset.order_by(ordering)
        if user_has_role(user, [ROLE_CADET]):
            cadet_statuses = [ComplaintStatus.PENDING_CADET_REVIEW, ComplaintStatus.RETURNED_TO_CADET]
            queryset = Complaint.objects.filter(status__in=cadet_statuses).filter(
                Q(assigned_cadet__isnull=True, status=ComplaintStatus.PENDING_CADET_REVIEW)
                | Q(assigned_cadet=user)
            )
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            return queryset.order_by(ordering)
        officer_statuses = [ComplaintStatus.PENDING_OFFICER_REVIEW]
        queryset = Complaint.objects.filter(status__in=officer_statuses, assigned_officer=user)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by(ordering)


class ComplaintResubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ComplaintResubmitSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        """Resubmit a returned complaint after corrections from the complainant."""

        complaint = get_object_or_404(Complaint, id=id, created_by=request.user)
        if complaint.status != ComplaintStatus.RETURNED_TO_COMPLAINANT:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not returned to complainant", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
        )
        serializer = ComplaintResubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(complaint, field, value)
        complaint.status = ComplaintStatus.PENDING_CADET_REVIEW
        complaint.last_message = ""
        complaint.save(update_fields=list(serializer.validated_data.keys()) + ["status", "last_message", "updated_at"])
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class CadetReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CADET]

    @extend_schema(request=CadetReviewSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        """Approve a complaint for officer review or return it to the complainant with a correction message."""

        complaint = get_object_or_404(Complaint, id=id)
        if complaint.status not in [ComplaintStatus.PENDING_CADET_REVIEW, ComplaintStatus.RETURNED_TO_CADET]:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not in cadet review", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if complaint.assigned_cadet_id and complaint.assigned_cadet_id != request.user.id:
            return Response(
                {"error": {"code": "forbidden", "message": "Complaint assigned to another cadet", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CadetReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        message = serializer.validated_data.get("message", "")
        complaint.assigned_cadet = request.user
        changed_fields = ["assigned_cadet"]
        if action == "return":
            complaint.strike_count += 1
            complaint.status = ComplaintStatus.VOIDED if complaint.strike_count >= 3 else ComplaintStatus.RETURNED_TO_COMPLAINANT
            complaint.last_message = message
            complaint.assigned_officer = None
            changed_fields.extend(["strike_count", "status", "last_message", "assigned_officer"])
            notification_type = "complaint_voided" if complaint.status == ComplaintStatus.VOIDED else "complaint_returned"
            Notification.objects.create(
                user=complaint.created_by,
                case=None,
                type=notification_type,
                payload={
                    "complaint_id": complaint.id,
                    "message": message,
                    "strike_count": complaint.strike_count,
                    "status": complaint.status,
                },
            )
        else:
            officer = get_object_or_404(User, id=serializer.validated_data["officer_id"])
            if not user_has_role(officer, [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER]):
                return Response(
                    {"error": {"code": "validation_error", "message": "Selected user is not an officer", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            complaint.status = ComplaintStatus.PENDING_OFFICER_REVIEW
            complaint.last_message = ""
            complaint.assigned_officer = officer
            changed_fields.extend(["status", "last_message", "assigned_officer"])
            Notification.objects.create(
                user=officer,
                case=None,
                type="complaint_forwarded_to_officer",
                payload={"complaint_id": complaint.id, "cadet_id": request.user.id},
            )
        complaint.save(update_fields=changed_fields + ["updated_at"])
        CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class OfficerReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER]

    @extend_schema(request=OfficerReviewSerializer, responses={200: ComplaintSerializer})
    def post(self, request, id):
        """Approve a complaint into a case or return it to the cadet for re-evaluation."""

        complaint = get_object_or_404(Complaint, id=id)
        if complaint.status != ComplaintStatus.PENDING_OFFICER_REVIEW:
            return Response(
                {"error": {"code": "invalid_state", "message": "Complaint not in officer review", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if complaint.assigned_officer_id != request.user.id:
            return Response(
                {"error": {"code": "forbidden", "message": "Complaint assigned to another officer", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OfficerReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        message = serializer.validated_data.get("message", "")
        if action == "return_to_cadet":
            if not complaint.assigned_cadet_id:
                return Response(
                    {"error": {"code": "invalid_state", "message": "No cadet assigned to receive this complaint", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            complaint.status = ComplaintStatus.RETURNED_TO_CADET
            complaint.last_message = message
            complaint.save(update_fields=["status", "last_message", "updated_at"])
            Notification.objects.create(
                user=complaint.assigned_cadet,
                case=None,
                type="complaint_returned_to_cadet",
                payload={"complaint_id": complaint.id, "message": message, "officer_id": request.user.id},
            )
            CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
            return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)
        primary_complainant = complaint.complainants.order_by("id").first()
        if not primary_complainant:
            return Response(
                {
                    "error": {
                        "code": "invalid_state",
                        "message": "Primary complainant is required before case formation",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if primary_complainant.verification_status != CaseComplainant.VerificationStatus.APPROVED:
            return Response(
                {
                    "error": {
                        "code": "invalid_state",
                        "message": "Primary complainant must be approved by cadet before case formation",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        approved_complainants = CaseComplainant.objects.filter(
            complaint=complaint,
            verification_status=CaseComplainant.VerificationStatus.APPROVED,
        )
        complaint.status = ComplaintStatus.APPROVED
        complaint.last_message = ""
        complaint.save(update_fields=["status", "last_message", "updated_at"])
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
        approved_complainants.update(case=case, is_verified=True)
        CaseAssignment.objects.get_or_create(case=case, user=request.user, role_in_case=CaseAssignmentRole.OFFICER)
        CaseReview.objects.create(complaint=complaint, reviewer=request.user, decision=action, message=message)
        return Response(ComplaintSerializer(complaint).data, status=status.HTTP_200_OK)


class CrimeSceneCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER, ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF]

    @extend_schema(request=CrimeSceneReportSerializer, responses={201: CrimeSceneActionResponseSerializer})
    def post(self, request):
        """Create a new case directly from a field crime-scene report and its witness records."""

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
        return Response(
            {"case": CaseSerializer(case).data, "crime_scene_report_id": report.id},
            status=status.HTTP_201_CREATED,
        )


class CrimeSceneApproveView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_POLICE_OFFICER, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF]

    @extend_schema(
        request=CrimeSceneApproveSerializer,
        responses={200: CrimeSceneActionResponseSerializer},
        operation_id="cases_crime_scene_approve_by_case",
    )
    def post(self, request, case_id):
        """Approve or reject a pending crime-scene case according to the required superior rank."""

        report = get_object_or_404(CrimeSceneReport, case_id=case_id)
        if report.status != CrimeSceneStatus.PENDING_APPROVAL:
            return Response(
                {"error": {"code": "invalid_state", "message": "Report not pending approval", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CrimeSceneApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        required_role = report.required_approver_role
        if report.reported_by_id == request.user.id:
            return Response(
                {"error": {"code": "forbidden", "message": "Case reporter cannot approve their own report", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
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
        return Response(
            {"case": CaseSerializer(report.case).data, "crime_scene_report_id": report.id},
            status=status.HTTP_200_OK,
        )


class CaseListView(generics.ListAPIView):
    """List cases accessible to the current user through assignments, ownership, or administrator access."""

    serializer_class = CaseSerializer

    def get_queryset(self):
        return _case_queryset_for_user(self.request.user)


class CaseDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve a case or update allowed fields, including validated status transitions for police roles."""

    serializer_class = CaseSerializer

    def get_queryset(self):
        return _case_queryset_for_user(self.request.user)

    def update(self, request, *args, **kwargs):
        case = self.get_object()
        if not user_has_role(request.user, list(POLICE_ROLES)):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized to update this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if "status" in request.data:
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
        """Attach a new complainant record to an existing case without additional verification."""

        case = get_object_or_404(Case, id=id)
        serializer = AddComplainantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CaseComplainant.objects.create(
            case=case,
            **serializer.validated_data,
            is_verified=True,
            verification_status=CaseComplainant.VerificationStatus.APPROVED,
            review_message="",
        )
        return Response(CaseSerializer(case).data, status=status.HTTP_200_OK)


class ComplainantReviewView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_CADET]

    @extend_schema(request=ComplainantReviewSerializer, responses={200: CaseComplainantSerializer})
    def post(self, request, id):
        """Approve or reject an individual complainant attached to a case or complaint."""

        complainant = get_object_or_404(CaseComplainant, id=id)
        if complainant.case_id and not complainant.complaint_id:
            return Response(
                {
                    "error": {
                        "code": "invalid_state",
                        "message": "Additional case complainants are auto-approved and do not require review",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ComplainantReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        message = serializer.validated_data.get("message", "").strip()
        if action == "approve":
            complainant.verification_status = CaseComplainant.VerificationStatus.APPROVED
            complainant.is_verified = True
            complainant.review_message = ""
        else:
            complainant.verification_status = CaseComplainant.VerificationStatus.REJECTED
            complainant.is_verified = False
            complainant.review_message = message
        complainant.save(update_fields=["verification_status", "is_verified", "review_message"])
        return Response(CaseComplainantSerializer(complainant).data, status=status.HTTP_200_OK)


class CaseAssignmentListCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]

    @extend_schema(request=None, responses={200: CaseAssignmentSerializer(many=True)})
    def get(self, request, case_id):
        """List current case assignments so managers can review the active investigation team."""

        case = get_object_or_404(Case, id=case_id)
        assignments = CaseAssignment.objects.filter(case=case).select_related("user")
        return Response(CaseAssignmentSerializer(assignments, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(request=CaseAssignmentUpsertSerializer, responses={200: CaseAssignmentSerializer, 201: CaseAssignmentSerializer})
    def post(self, request, case_id):
        """Assign a user to a case role when their system role satisfies the assignment rules."""

        case = get_object_or_404(Case, id=case_id)
        serializer = CaseAssignmentUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, id=serializer.validated_data["user_id"])
        role_in_case = serializer.validated_data["role_in_case"]
        required_role_map = {
            CaseAssignmentRole.DETECTIVE: [ROLE_DETECTIVE],
            CaseAssignmentRole.OFFICER: [ROLE_POLICE_OFFICER, ROLE_PATROL_OFFICER],
            CaseAssignmentRole.SERGEANT: [ROLE_SERGEANT],
        }
        if not user_has_role(user, required_role_map.get(role_in_case, [])):
            return Response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "User does not have required system role for this assignment",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment, created = CaseAssignment.objects.get_or_create(
            case=case,
            user=user,
            role_in_case=role_in_case,
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(CaseAssignmentSerializer(assignment).data, status=status_code)


class CaseAssignmentDeleteView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, case_id, id):
        """Remove a specific assignment from a case."""

        case = get_object_or_404(Case, id=case_id)
        assignment = get_object_or_404(CaseAssignment, id=id, case=case)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
