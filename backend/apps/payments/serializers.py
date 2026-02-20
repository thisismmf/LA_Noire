from rest_framework import serializers
from .models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    person_id = serializers.IntegerField(required=False)
    amount = serializers.IntegerField()
    type = serializers.ChoiceField(choices=["bail", "fine"])


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "payer", "case", "person", "amount", "type", "status", "gateway_ref", "created_at", "verified_at")
        read_only_fields = fields


class PaymentCallbackSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["success", "failed"])
    signature = serializers.CharField()
