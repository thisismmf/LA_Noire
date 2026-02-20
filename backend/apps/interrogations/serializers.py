from rest_framework import serializers
from .models import Interrogation


class InterrogationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interrogation
        fields = (
            "id",
            "case",
            "suspect",
            "detective_score",
            "sergeant_score",
            "captain_decision",
            "captain_notes",
            "chief_decision",
            "chief_notes",
            "status",
        )
        read_only_fields = ("id", "status")


class InterrogationCreateSerializer(serializers.Serializer):
    suspect_id = serializers.IntegerField()
    detective_score = serializers.IntegerField(required=False)

    def validate_detective_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Score must be between 1 and 10")
        return value


class ScoreSerializer(serializers.Serializer):
    score = serializers.IntegerField()

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Score must be between 1 and 10")
        return value


class CaptainDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    notes = serializers.CharField(required=False, allow_blank=True)


class ChiefDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    notes = serializers.CharField(required=False, allow_blank=True)
