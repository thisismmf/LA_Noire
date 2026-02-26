from rest_framework import serializers
from django.utils import timezone
from .models import (
    Complaint,
    Case,
    CaseComplainant,
    CaseReview,
    CrimeSceneReport,
    CrimeSceneWitness,
    CaseAssignment,
)
from .constants import ComplaintStatus, CaseStatus, CrimeSceneStatus, CaseSourceType


class CaseComplainantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseComplainant
        fields = ("id", "full_name", "phone", "national_id", "is_verified", "verification_status", "review_message")
        read_only_fields = ("id", "is_verified", "verification_status", "review_message")


class ComplaintSerializer(serializers.ModelSerializer):
    complainants = CaseComplainantSerializer(many=True, required=False)

    class Meta:
        model = Complaint
        fields = (
            "id",
            "title",
            "description",
            "crime_level",
            "location",
            "incident_datetime",
            "status",
            "strike_count",
            "last_message",
            "complainants",
            "created_at",
        )
        read_only_fields = ("id", "status", "strike_count", "last_message", "created_at")

    def create(self, validated_data):
        complainants_data = validated_data.pop("complainants", [])
        complaint = Complaint.objects.create(**validated_data)
        for comp in complainants_data:
            CaseComplainant.objects.create(complaint=complaint, **comp)
        return complaint


class ComplaintResubmitSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    crime_level = serializers.IntegerField(required=False)
    location = serializers.CharField(required=False)
    incident_datetime = serializers.DateTimeField(required=False, allow_null=True)


class CadetReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "return"])
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get("action")
        message = (attrs.get("message") or "").strip()
        if action == "return" and not message:
            raise serializers.ValidationError("message is required when returning to complainant")
        return attrs


class OfficerReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "return_to_cadet"])
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get("action")
        message = (attrs.get("message") or "").strip()
        if action == "return_to_cadet" and not message:
            raise serializers.ValidationError("message is required when returning to cadet")
        return attrs


class CrimeSceneWitnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeSceneWitness
        fields = ("full_name", "phone", "national_id")


class CrimeSceneReportSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    crime_level = serializers.IntegerField()
    location = serializers.CharField()
    incident_datetime = serializers.DateTimeField(required=False, allow_null=True)
    scene_datetime = serializers.DateTimeField()
    witnesses = CrimeSceneWitnessSerializer(many=True)


class CrimeSceneApproveSerializer(serializers.Serializer):
    approve = serializers.BooleanField()


class CaseSerializer(serializers.ModelSerializer):
    complainants = CaseComplainantSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = (
            "id",
            "title",
            "description",
            "crime_level",
            "location",
            "incident_datetime",
            "status",
            "source_type",
            "created_at",
            "complainants",
        )
        read_only_fields = ("id", "created_at")


class AddComplainantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseComplainant
        fields = ("full_name", "phone", "national_id")


class ComplainantReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get("action")
        message = (attrs.get("message") or "").strip()
        if action == "reject" and not message:
            raise serializers.ValidationError("message is required when rejecting complainant")
        return attrs


class CaseAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseAssignment
        fields = ("id", "case", "user", "role_in_case", "assigned_at")
        read_only_fields = ("id", "assigned_at")


class CaseAssignmentUpsertSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_in_case = serializers.ChoiceField(choices=[choice[0] for choice in CaseAssignment._meta.get_field("role_in_case").choices])
