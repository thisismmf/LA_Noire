import hashlib
import hmac
import uuid
from django.conf import settings


def generate_gateway_ref():
    return uuid.uuid4().hex


def sign_payload(payload: str) -> str:
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(payload: str, signature: str) -> bool:
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)
