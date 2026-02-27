from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_SERGEANT
from apps.cases.models import Case
from apps.cases.constants import CrimeLevel
from apps.suspects.models import Person, WantedRecord
from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer, PaymentCallbackSerializer, PaymentCreateResponseSerializer
from .gateway import build_callback_url, request_payment, verify_payment, PaymentGatewayError


def _set_payment_status(payment, status_value):
    payment.status = status_value
    payment.verified_at = timezone.now()
    payment.save(update_fields=["status", "verified_at"])


def _verify_and_update_payment(payment, authority):
    if not authority:
        return False, {"code": "validation_error", "message": "Authority is required for verification"}
    if payment.gateway_ref and payment.gateway_ref != authority:
        return False, {"code": "invalid_authority", "message": "Authority does not match payment record"}
    if payment.status == "success":
        return True, {"code": 101, "message": "Payment already verified"}
    try:
        verification = verify_payment(amount=payment.amount, authority=authority)
    except PaymentGatewayError as exc:
        return False, {"code": "gateway_error", "message": str(exc)}
    if verification["ok"]:
        payment.gateway_ref = authority
        payment.status = "success"
        payment.verified_at = timezone.now()
        payment.save(update_fields=["gateway_ref", "status", "verified_at"])
        return True, verification
    _set_payment_status(payment, "failed")
    return False, verification


class PaymentCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SERGEANT]

    @extend_schema(request=PaymentCreateSerializer, responses={201: PaymentCreateResponseSerializer})
    def post(self, request):
        """Create a bail or fine payment request and return the gateway redirect payload."""

        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = get_object_or_404(Case, id=serializer.validated_data["case_id"])
        payment_type = serializer.validated_data["type"]
        person = get_object_or_404(Person, id=serializer.validated_data["person_id"])
        wanted_record = WantedRecord.objects.filter(case=case, person=person).first()
        if not wanted_record:
            return Response(
                {"error": {"code": "validation_error", "message": "Person is not linked to this case", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if payment_type == "bail":
            if case.crime_level not in [CrimeLevel.LEVEL_3, CrimeLevel.LEVEL_2]:
                return Response(
                    {"error": {"code": "validation_error", "message": "Bail only for Level 2/3", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if wanted_record.status not in ["wanted", "arrested"]:
                return Response(
                    {"error": {"code": "validation_error", "message": "Bail requires suspect status in case", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if payment_type == "fine":
            if case.crime_level != CrimeLevel.LEVEL_3:
                return Response(
                    {"error": {"code": "validation_error", "message": "Fine only for Level 3", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if wanted_record.status != "arrested":
                return Response(
                    {"error": {"code": "validation_error", "message": "Fine requires arrested criminal status in case", "details": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        payment = Payment.objects.create(
            payer=None,
            case=case,
            person=person,
            amount=serializer.validated_data["amount"],
            type=payment_type,
            status="pending",
            gateway_ref="",
        )
        callback_url = build_callback_url(payment.id)
        description = f"{payment_type.title()} payment for case #{case.id} and person #{person.id}"
        try:
            gateway_response = request_payment(
                payment_id=payment.id,
                amount=payment.amount,
                description=description,
                callback_url=callback_url,
                mobile=person.phone or None,
            )
        except PaymentGatewayError as exc:
            _set_payment_status(payment, "failed")
            return Response(
                {"error": {"code": "gateway_error", "message": str(exc), "details": {}}},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not gateway_response["ok"]:
            _set_payment_status(payment, "failed")
            return Response(
                {
                    "error": {
                        "code": "gateway_rejected",
                        "message": gateway_response.get("message", "Gateway rejected payment request"),
                        "details": {"gateway_code": gateway_response.get("code")},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment.gateway_ref = gateway_response["authority"]
        payment.save(update_fields=["gateway_ref"])
        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "redirect_url": gateway_response["redirect_url"],
                "authority": gateway_response["authority"],
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentReturnView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: OpenApiTypes.STR})
    def get(self, request):
        """Handle Zarinpal return redirect and render the final payment result page."""

        payment_id = request.GET.get("payment_id")
        status_param = request.GET.get("Status") or request.GET.get("status", "NOK")
        authority = request.GET.get("Authority") or request.GET.get("authority")
        payment = Payment.objects.filter(id=payment_id).first() if payment_id else None
        context = {
            "payment": payment,
            "status": "failed",
            "authority": authority,
            "message": "Payment record not found.",
            "ref_id": None,
        }
        if not payment:
            return render(request, "payments/return.html", context)

        if str(status_param).upper() != "OK":
            if payment.status != "success":
                _set_payment_status(payment, "failed")
            context.update({"status": "failed", "message": "Payment was canceled or failed on gateway side."})
            return render(request, "payments/return.html", context)

        verified, verify_result = _verify_and_update_payment(payment, authority)
        context.update(
            {
                "status": "success" if verified else "failed",
                "message": verify_result.get("message", "Verification failed."),
                "ref_id": verify_result.get("ref_id"),
            }
        )
        return render(request, "payments/return.html", context)


class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=PaymentCallbackSerializer, responses={200: PaymentSerializer})
    def post(self, request):
        """Verify a Zarinpal callback payload and persist the payment status."""

        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = get_object_or_404(Payment, id=serializer.validated_data["payment_id"])
        status_value = str(serializer.validated_data.get("status", "OK")).upper()
        authority = serializer.validated_data.get("authority")

        if status_value in {"NOK", "FAILED", "FAIL"}:
            _set_payment_status(payment, "failed")
            return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

        verified, verify_result = _verify_and_update_payment(payment, authority)
        if not verified:
            return Response(
                {
                    "error": {
                        "code": verify_result.get("code", "verification_failed"),
                        "message": verify_result.get("message", "Payment verification failed"),
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
