from urllib.parse import urlencode

import requests
from django.conf import settings


class PaymentGatewayError(Exception):
    pass


def _extract_error_message(errors):
    if isinstance(errors, dict):
        return errors.get("message")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            return first.get("message") or first.get("code")
        return str(first)
    return None


def _zarinpal_host():
    return "sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "payment.zarinpal.com"


def _zarinpal_request_url():
    return f"https://{_zarinpal_host()}/pg/v4/payment/request.json"


def _zarinpal_verify_url():
    return f"https://{_zarinpal_host()}/pg/v4/payment/verify.json"


def _zarinpal_startpay_url(authority):
    return f"https://{_zarinpal_host()}/pg/StartPay/{authority}"


def build_callback_url(payment_id):
    base = settings.PAYMENT_CALLBACK_BASE_URL.rstrip("/")
    query = urlencode({"payment_id": payment_id})
    return f"{base}/api/v1/payments/return/?{query}"


def request_payment(*, payment_id, amount, description, callback_url, mobile=None, email=None):
    provider = settings.PAYMENT_GATEWAY_PROVIDER
    if provider == "mock":
        authority = f"S{payment_id:08d}"
        return {
            "ok": True,
            "authority": authority,
            "code": 100,
            "message": "Mock payment created",
            "redirect_url": _zarinpal_startpay_url(authority),
        }
    if provider != "zarinpal":
        raise PaymentGatewayError("Unsupported payment gateway provider")

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(amount),
        "description": description,
        "callback_url": callback_url,
    }
    metadata = {}
    if mobile:
        metadata["mobile"] = mobile
    if email:
        metadata["email"] = email
    if metadata:
        payload["metadata"] = metadata

    try:
        response = requests.post(_zarinpal_request_url(), json=payload, timeout=settings.ZARINPAL_TIMEOUT)
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        raise PaymentGatewayError(f"Zarinpal request API failed: {exc}") from exc
    except ValueError as exc:
        raise PaymentGatewayError("Zarinpal request API returned invalid JSON") from exc

    data = body.get("data") or {}
    errors = body.get("errors") or {}
    code = data.get("code")
    authority = data.get("authority")
    if code == 100 and authority:
        return {
            "ok": True,
            "authority": authority,
            "code": code,
            "message": data.get("message", "Success"),
            "redirect_url": _zarinpal_startpay_url(authority),
        }

    error_message = data.get("message") or _extract_error_message(errors) or "Payment request rejected by gateway"
    return {
        "ok": False,
        "authority": None,
        "code": code,
        "message": str(error_message),
        "errors": errors,
    }


def verify_payment(*, amount, authority):
    provider = settings.PAYMENT_GATEWAY_PROVIDER
    if provider == "mock":
        return {
            "ok": True,
            "code": 100,
            "message": "Mock verification success",
            "ref_id": 100000 + (int("".join(filter(str.isdigit, authority))) if any(ch.isdigit() for ch in authority) else 0),
            "raw": {"data": {"code": 100, "message": "Mock verification success", "ref_id": 100001}, "errors": []},
        }
    if provider != "zarinpal":
        raise PaymentGatewayError("Unsupported payment gateway provider")

    payload = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(amount),
        "authority": authority,
    }
    try:
        response = requests.post(_zarinpal_verify_url(), json=payload, timeout=settings.ZARINPAL_TIMEOUT)
        response.raise_for_status()
        body = response.json()
    except requests.RequestException as exc:
        raise PaymentGatewayError(f"Zarinpal verify API failed: {exc}") from exc
    except ValueError as exc:
        raise PaymentGatewayError("Zarinpal verify API returned invalid JSON") from exc

    data = body.get("data") or {}
    errors = body.get("errors") or {}
    code = data.get("code")
    ref_id = data.get("ref_id")
    ok = code in (100, 101)
    message = data.get("message") or _extract_error_message(errors) or ("Verified" if ok else "Verification failed")
    return {
        "ok": ok,
        "code": code,
        "message": str(message),
        "ref_id": ref_id,
        "raw": body,
    }
