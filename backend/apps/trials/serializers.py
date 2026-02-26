from rest_framework import serializers
from .models import Trial


class TrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trial
        fields = ("id", "case", "judge", "verdict", "punishment_title", "punishment_description", "decided_at")
        read_only_fields = ("id", "judge", "decided_at")


class TrialDecisionSerializer(serializers.Serializer):
    verdict = serializers.ChoiceField(choices=["guilty", "not_guilty"])
    punishment_title = serializers.CharField(required=False, allow_blank=True)
    punishment_description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get("verdict") == "guilty" and not attrs.get("punishment_title"):
            raise serializers.ValidationError("punishment_title is required for guilty verdict")
        return attrs


class CaseReportResponseSerializer(serializers.Serializer):
    case = serializers.DictField()
    complaint = serializers.DictField(allow_null=True)
    crime_scene_report = serializers.DictField(allow_null=True)
    reviews = serializers.ListField(child=serializers.DictField())
    evidence = serializers.ListField(child=serializers.DictField())
    suspects = serializers.ListField(child=serializers.DictField())
    interrogations = serializers.ListField(child=serializers.DictField())
    assignments = serializers.ListField(child=serializers.DictField())
