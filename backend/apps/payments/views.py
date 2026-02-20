from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_SERGEANT
from apps.cases.models import Case
from apps.cases.constants import CrimeLevel
from apps.suspects.models import Person
from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer, PaymentCallbackSerializer
from .gateway import generate_gateway_ref, sign_payload, verify_signature


class PaymentCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, id=serializer.validated_data["case_id"])
        payment_type = serializer.validated_data["type"]
        if payment_type == "bail" and case.crime_level not in [CrimeLevel.LEVEL_3, CrimeLevel.LEVEL_2]:
            return Response(
                {"error": {"code": "validation_error", "message": "Bail only for Level 2/3", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if payment_type == "fine" and case.crime_level != CrimeLevel.LEVEL_3:
            return Response(
                {"error": {"code": "validation_error", "message": "Fine only for Level 3", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        person = None
        if serializer.validated_data.get("person_id"):
            person = get_object_or_404(Person, id=serializer.validated_data["person_id"])
        payment = Payment.objects.create(
            payer=None,
            case=case,
            person=person,
            amount=serializer.validated_data["amount"],
            type=payment_type,
            status="pending",
            gateway_ref=generate_gateway_ref(),
        )
        payload = f"{payment.id}:{payment.amount}:{payment.type}"
        signature = sign_payload(payload)
        redirect_url = f"/api/v1/payments/return/?payment_id={payment.id}&status=pending"
        return Response({"payment": PaymentSerializer(payment).data, "redirect_url": redirect_url, "signature": signature}, status=status.HTTP_201_CREATED)


class PaymentReturnView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payment_id = request.GET.get("payment_id")
        status_param = request.GET.get("status", "pending")
        payment = Payment.objects.filter(id=payment_id).first() if payment_id else None
        return render(request, "payments/return.html", {"payment": payment, "status": status_param})


class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = get_object_or_404(Payment, id=serializer.validated_data["payment_id"])
        payload = f"{payment.id}:{payment.amount}:{payment.type}"
        if not verify_signature(payload, serializer.validated_data["signature"]):
            return Response(
                {"error": {"code": "invalid_signature", "message": "Signature mismatch", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        status_value = serializer.validated_data["status"]
        payment.status = "success" if status_value == "success" else "failed"
        payment.verified_at = timezone.now()
        payment.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
