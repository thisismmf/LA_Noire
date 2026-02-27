from rest_framework import serializers
from .models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    person_id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(min_value=1)
    type = serializers.ChoiceField(choices=["bail", "fine"])


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "payer", "case", "person", "amount", "type", "status", "gateway_ref", "created_at", "verified_at")
        read_only_fields = fields


class PaymentCallbackSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    authority = serializers.CharField(required=False)
    status = serializers.CharField(required=False)

    def validate_status(self, value):
        normalized = str(value).upper()
        allowed = {"OK", "NOK", "SUCCESS", "FAILED", "FAIL"}
        if normalized not in allowed:
            raise serializers.ValidationError("status must be one of OK, NOK, SUCCESS, FAILED, FAIL")
        return normalized


class PaymentCreateResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer()
    redirect_url = serializers.CharField()
    authority = serializers.CharField()
