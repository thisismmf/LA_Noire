from rest_framework import serializers
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


class EvidenceMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceMedia
        fields = ("id", "file", "media_type")
        read_only_fields = ("id",)


class WitnessStatementEvidenceSerializer(serializers.ModelSerializer):
    media = EvidenceMediaSerializer(many=True, required=False)

    class Meta:
        model = WitnessStatementEvidence
        fields = ("transcription", "media")


class MedicalEvidenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalEvidenceImage
        fields = ("id", "image")
        read_only_fields = ("id",)


class MedicalEvidenceSerializer(serializers.ModelSerializer):
    images = MedicalEvidenceImageSerializer(many=True, required=False)

    class Meta:
        model = MedicalEvidence
        fields = ("forensic_result", "identity_db_result", "status", "images")


class VehicleEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEvidence
        fields = ("model", "color", "license_plate", "serial_number")

    def validate(self, attrs):
        license_plate = attrs.get("license_plate")
        serial_number = attrs.get("serial_number")
        if license_plate and serial_number:
            raise serializers.ValidationError("license_plate and serial_number cannot both be set")
        if not license_plate and not serial_number:
            raise serializers.ValidationError("license_plate or serial_number is required")
        return attrs


class IdentityDocumentEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDocumentEvidence
        fields = ("owner_full_name", "data")


class EvidenceSerializer(serializers.ModelSerializer):
    witness_statement = WitnessStatementEvidenceSerializer(required=False)
    medical = MedicalEvidenceSerializer(required=False)
    vehicle = VehicleEvidenceSerializer(required=False)
    identity_document = IdentityDocumentEvidenceSerializer(required=False)

    class Meta:
        model = Evidence
        fields = (
            "id",
            "case",
            "title",
            "description",
            "evidence_type",
            "created_at",
            "created_by",
            "witness_statement",
            "medical",
            "vehicle",
            "identity_document",
        )
        read_only_fields = ("id", "created_at", "created_by")


class EvidenceCreateSerializer(serializers.Serializer):
    evidence_type = serializers.ChoiceField(choices=EvidenceType.choices)
    title = serializers.CharField()
    description = serializers.CharField(required=True, allow_blank=False)
    witness_statement = WitnessStatementEvidenceSerializer(required=False)
    medical = MedicalEvidenceSerializer(required=False)
    vehicle = VehicleEvidenceSerializer(required=False)
    identity_document = IdentityDocumentEvidenceSerializer(required=False)

    def validate(self, attrs):
        evidence_type = attrs.get("evidence_type")
        if evidence_type == EvidenceType.WITNESS_STATEMENT and not attrs.get("witness_statement"):
            raise serializers.ValidationError("witness_statement data is required")
        if evidence_type == EvidenceType.MEDICAL and not attrs.get("medical"):
            raise serializers.ValidationError("medical data is required")
        if evidence_type == EvidenceType.VEHICLE and not attrs.get("vehicle"):
            raise serializers.ValidationError("vehicle data is required")
        if evidence_type == EvidenceType.IDENTITY_DOCUMENT and not attrs.get("identity_document"):
            raise serializers.ValidationError("identity_document data is required")
        return attrs
