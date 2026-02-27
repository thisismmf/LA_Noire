from rest_framework import serializers
from .models import Person, SuspectCandidate, WantedRecord


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ("id", "full_name", "national_id", "phone", "photo", "notes")


class SuspectCandidateSerializer(serializers.ModelSerializer):
    person = PersonSerializer()

    class Meta:
        model = SuspectCandidate
        fields = ("id", "case", "person", "rationale", "status", "sergeant_message", "decided_at")
        read_only_fields = ("id", "status", "sergeant_message", "decided_at")


class SuspectProposalSerializer(serializers.Serializer):
    suspects = PersonSerializer(many=True)
    rationale = serializers.CharField()


class SergeantDecisionSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("approve") and not (attrs.get("message") or "").strip():
            raise serializers.ValidationError("message is required when rejecting a suspect")
        return attrs


class WantedRecordSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)

    class Meta:
        model = WantedRecord
        fields = ("id", "person", "case", "started_at", "ended_at", "status")


class MostWantedSerializer(serializers.Serializer):
    person = PersonSerializer()
    days_wanted = serializers.IntegerField()
    crime_degree = serializers.IntegerField()
    ranking_score = serializers.IntegerField()
    reward_amount = serializers.IntegerField()


class SuspectStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["wanted", "arrested", "cleared"])
    case_id = serializers.IntegerField()
