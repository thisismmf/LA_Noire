from rest_framework import serializers
from apps.accounts.models import User
from .models import (
    Complaint,
    Case,
    CaseComplainant,
    CaseReview,
    CrimeSceneReport,
    CrimeSceneWitness,
    CaseAssignment,
)


def _normalize_name(value):
    return " ".join((value or "").strip().lower().split())


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
            "assigned_cadet",
            "assigned_officer",
            "complainants",
            "created_at",
        )
        read_only_fields = ("id", "status", "strike_count", "last_message", "assigned_cadet", "assigned_officer", "created_at")

    def validate_complainants(self, value):
        if len(value) > 1:
            raise serializers.ValidationError("Only the primary complainant can be submitted initially")
        return value

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
    officer_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        action = attrs.get("action")
        message = (attrs.get("message") or "").strip()
        if action == "return" and not message:
            raise serializers.ValidationError("message is required when returning to complainant")
        if action == "approve" and not attrs.get("officer_id"):
            raise serializers.ValidationError("officer_id is required when forwarding to an officer")
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

    def validate_witnesses(self, witnesses):
        validated_witnesses = []
        for witness in witnesses:
            national_id = witness.get("national_id")
            phone = witness.get("phone")
            matched_user = User.objects.filter(national_id=national_id).first()
            if not matched_user:
                raise serializers.ValidationError(
                    f"Witness with national_id '{national_id}' must exist in the database"
                )
            if matched_user.phone != phone:
                raise serializers.ValidationError(
                    f"Witness phone for national_id '{national_id}' does not match the database"
                )
            expected_full_name = f"{matched_user.first_name} {matched_user.last_name}".strip()
            provided_full_name = witness.get("full_name", "")
            if provided_full_name and _normalize_name(provided_full_name) != _normalize_name(expected_full_name):
                raise serializers.ValidationError(
                    f"Witness full_name for national_id '{national_id}' does not match the database"
                )
            witness["full_name"] = provided_full_name or expected_full_name
            validated_witnesses.append(witness)
        return validated_witnesses


class CrimeSceneApproveSerializer(serializers.Serializer):
    approve = serializers.BooleanField()


class CrimeSceneActionResponseSerializer(serializers.Serializer):
    case = serializers.DictField()
    crime_scene_report_id = serializers.IntegerField()


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
