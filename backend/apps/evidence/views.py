from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import (
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
)
from apps.rbac.utils import user_has_role
from apps.cases.models import Case, CaseAssignment
from apps.cases.policies import can_user_access_case
from apps.notifications.models import Notification
from .models import (
    Evidence,
    EvidenceType,
    WitnessStatementEvidence,
    EvidenceMedia,
    MedicalEvidence,
    MedicalEvidenceImage,
    VehicleEvidence,
    IdentityDocumentEvidence,
)
from .serializers import EvidenceSerializer, EvidenceCreateSerializer


ALLOWED_EVIDENCE_ROLES = [
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
]


class EvidenceListCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = ALLOWED_EVIDENCE_ROLES

    @extend_schema(request=EvidenceCreateSerializer, responses={201: EvidenceSerializer})
    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_has_role(request.user, [ROLE_DETECTIVE]) and not CaseAssignment.objects.filter(
            case=case, user=request.user, role_in_case="detective"
        ).exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = EvidenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence_type = serializer.validated_data["evidence_type"]
        if evidence_type == EvidenceType.MEDICAL:
            med_data = serializer.validated_data["medical"]
            images = med_data.get("images", [])
            if not images:
                return Response(
                    {"error": {"code": "validation_error", "message": "Medical evidence requires images", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        evidence = Evidence.objects.create(
            case=case,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            evidence_type=evidence_type,
            created_by=request.user,
        )
        if evidence_type == EvidenceType.WITNESS_STATEMENT:
            ws_data = serializer.validated_data["witness_statement"]
            ws = WitnessStatementEvidence.objects.create(evidence=evidence, transcription=ws_data["transcription"])
            for media in ws_data.get("media", []):
                EvidenceMedia.objects.create(witness_statement=ws, **media)
        elif evidence_type == EvidenceType.MEDICAL:
            med_data = serializer.validated_data["medical"]
            med = MedicalEvidence.objects.create(
                evidence=evidence,
                forensic_result=med_data.get("forensic_result", ""),
                identity_db_result=med_data.get("identity_db_result", ""),
                status=med_data.get("status", "pending"),
            )
            images = med_data.get("images", [])
            for img in images:
                MedicalEvidenceImage.objects.create(medical_evidence=med, image=img["image"])
        elif evidence_type == EvidenceType.VEHICLE:
            VehicleEvidence.objects.create(evidence=evidence, **serializer.validated_data["vehicle"])
        elif evidence_type == EvidenceType.IDENTITY_DOCUMENT:
            IdentityDocumentEvidence.objects.create(evidence=evidence, **serializer.validated_data["identity_document"])

        self._notify_detectives(case, evidence)
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)

    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_has_role(request.user, [ROLE_DETECTIVE]) and not CaseAssignment.objects.filter(
            case=case, user=request.user, role_in_case="detective"
        ).exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = Evidence.objects.filter(case=case)
        evidence_type = request.query_params.get("type")
        if evidence_type:
            queryset = queryset.filter(evidence_type=evidence_type)
        data = EvidenceSerializer(queryset, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def _notify_detectives(self, case, evidence):
        detective_assignments = CaseAssignment.objects.filter(case=case, role_in_case="detective")
        for assignment in detective_assignments:
            Notification.objects.create(
                user=assignment.user,
                case=case,
                type="new_evidence",
                payload={"evidence_id": evidence.id, "evidence_type": evidence.evidence_type},
            )


class EvidenceDetailView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = ALLOWED_EVIDENCE_ROLES

    def get(self, request, id):
        evidence = get_object_or_404(Evidence, id=id)
        if not can_user_access_case(request.user, evidence.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_has_role(request.user, [ROLE_DETECTIVE]) and not CaseAssignment.objects.filter(
            case=evidence.case, user=request.user, role_in_case="detective"
        ).exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        evidence = get_object_or_404(Evidence, id=id)
        if not can_user_access_case(request.user, evidence.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_has_role(request.user, [ROLE_DETECTIVE]) and not CaseAssignment.objects.filter(
            case=evidence.case, user=request.user, role_in_case="detective"
        ).exists():
            return Response(
                {"error": {"code": "forbidden", "message": "Detective not assigned to case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        data = request.data
        if evidence.evidence_type == EvidenceType.MEDICAL:
            if "forensic_result" in data or "status" in data:
                if not user_has_role(request.user, [ROLE_CORONER, ROLE_SYSTEM_ADMIN]):
                    return Response(
                        {"error": {"code": "forbidden", "message": "Coroner role required", "details": {}}},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                medical = evidence.medical
                if "forensic_result" in data:
                    medical.forensic_result = data.get("forensic_result", medical.forensic_result)
                if "status" in data:
                    medical.status = data.get("status", medical.status)
                medical.save()
            if "identity_db_result" in data:
                if not user_has_role(request.user, [ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]):
                    return Response(
                        {"error": {"code": "forbidden", "message": "Admin role required", "details": {}}},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                medical = evidence.medical
                medical.identity_db_result = data.get("identity_db_result", medical.identity_db_result)
                medical.save()
        if "title" in data:
            evidence.title = data["title"]
        if "description" in data:
            evidence.description = data["description"]
        evidence.save()
        if evidence.evidence_type == EvidenceType.WITNESS_STATEMENT and "witness_statement" in data:
            ws_data = data.get("witness_statement", {})
            ws = evidence.witness_statement
            if "transcription" in ws_data:
                ws.transcription = ws_data["transcription"]
                ws.save()
        if evidence.evidence_type == EvidenceType.VEHICLE and "vehicle" in data:
            vehicle_data = data.get("vehicle", {})
            vehicle = evidence.vehicle
            for field in ["model", "color", "license_plate", "serial_number"]:
                if field in vehicle_data:
                    setattr(vehicle, field, vehicle_data[field])
            if vehicle.license_plate and vehicle.serial_number:
                return Response(
                    {"error": {"code": "validation_error", "message": "license_plate and serial_number cannot both be set", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not vehicle.license_plate and not vehicle.serial_number:
                return Response(
                    {"error": {"code": "validation_error", "message": "license_plate or serial_number is required", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            vehicle.save()
        if evidence.evidence_type == EvidenceType.IDENTITY_DOCUMENT and "identity_document" in data:
            identity_data = data.get("identity_document", {})
            identity = evidence.identity_document
            if "owner_full_name" in identity_data:
                identity.owner_full_name = identity_data["owner_full_name"]
            if "data" in identity_data:
                identity.data = identity_data["data"]
            identity.save()
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        evidence = get_object_or_404(Evidence, id=id)
        if not can_user_access_case(request.user, evidence.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user_has_role(request.user, [ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_SYSTEM_ADMIN]):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        evidence.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
