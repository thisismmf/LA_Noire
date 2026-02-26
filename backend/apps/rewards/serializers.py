from rest_framework import serializers
from .models import Tip, TipAttachment, RewardCode


class TipAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipAttachment
        fields = ("id", "file")
        read_only_fields = ("id",)


class TipSerializer(serializers.ModelSerializer):
    attachments = TipAttachmentSerializer(many=True, required=False)

    class Meta:
        model = Tip
        fields = (
            "id",
            "case",
            "person",
            "content",
            "status",
            "created_at",
            "attachments",
        )
        read_only_fields = ("id", "status", "created_at")


class OfficerReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        ref_name = "TipOfficerReview"


class DetectiveReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        ref_name = "TipDetectiveReview"


class RewardCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardCode
        fields = ("code", "amount", "issued_at", "redeemed_at")
        read_only_fields = fields


class RewardLookupSerializer(serializers.Serializer):
    national_id = serializers.CharField()
    code = serializers.CharField()


class RewardLookupUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    national_id = serializers.CharField()


class RewardLookupTipSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()
    status = serializers.CharField()


class RewardLookupResultSerializer(serializers.Serializer):
    code = serializers.CharField()
    issued_at = serializers.DateTimeField()
    redeemed_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    amount = serializers.IntegerField()


class RewardLookupResponseSerializer(serializers.Serializer):
    user = RewardLookupUserSerializer()
    tip = RewardLookupTipSerializer()
    reward = RewardLookupResultSerializer()
