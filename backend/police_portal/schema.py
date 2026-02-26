import inspect
from collections.abc import Mapping

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings


GENERIC_ERROR_EXAMPLE = OpenApiExample(
    "Error Response",
    value={
        "error": {
            "code": "validation_error",
            "message": "Readable message",
            "details": {"field": ["This field is required."]},
        }
    },
    response_only=True,
)

FIELD_NAME_EXAMPLES = {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
    "action": "approve",
    "amount": 1000,
    "approve": True,
    "case_id": 1,
    "code": "RW-1024",
    "color": "Black",
    "content": "Citizen tip about suspect location",
    "crime_level": "level_2",
    "description": "Detailed operational note for investigators.",
    "email": "officer@example.com",
    "first_name": "Cole",
    "forensic_result": "Fingerprint match pending confirmation.",
    "full_name": "John Doe",
    "gateway_ref": "GW-20260226-0001",
    "id": 1,
    "identifier": "officer@example.com",
    "identity_db_result": "Record matched in identity database.",
    "incident_datetime": "2026-02-26T10:30:00Z",
    "last_name": "Phelps",
    "license_plate": "LAPD-1024",
    "location": "Downtown Los Angeles",
    "message": "Approved after supervisor review.",
    "model": "Buick Eight",
    "national_id": "A123456789",
    "password": "Pass1234!",
    "payment_id": 1,
    "person_id": 1,
    "phone": "5551234567",
    "ranking_score": 120,
    "redirect_url": "/api/v1/payments/return/?payment_id=1&status=pending",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
    "rationale": "Witness testimony and vehicle footage point to this suspect.",
    "role": "detective",
    "role_in_case": "detective",
    "score": 8,
    "serial_number": "VIN123456789",
    "signature": "signed-payload-example",
    "status": "pending",
    "title": "Armed robbery investigation",
    "transcription": "Witness states the suspect fled in a dark sedan.",
    "type": "bail",
    "username": "detective_01",
    "verdict": "guilty",
}


def _instantiate_serializer(serializer_like):
    if serializer_like in (None, OpenApiTypes.NONE):
        return None
    if inspect.isclass(serializer_like) and issubclass(serializer_like, serializers.BaseSerializer):
        return serializer_like()
    return serializer_like


def _first_choice(field):
    choices = getattr(field, "choices", None)
    if not choices:
        return None
    if isinstance(choices, Mapping):
        return next(iter(choices.keys()), None)
    return next(iter(choices), None)


def _string_example(field_name):
    if field_name in FIELD_NAME_EXAMPLES:
        return FIELD_NAME_EXAMPLES[field_name]
    if field_name.endswith("_url"):
        return "https://example.com/resource"
    if field_name.endswith("_at") or field_name.endswith("_datetime"):
        return "2026-02-26T10:30:00Z"
    if field_name.endswith("_date"):
        return "2026-02-26"
    if field_name.endswith("_id"):
        return 1
    return "example"


def _build_field_example(field_name, field, *, include_read_only):
    if isinstance(field, serializers.HiddenField):
        return None
    choice_value = _first_choice(field)
    if choice_value is not None:
        return choice_value
    if isinstance(field, serializers.ListSerializer):
        child_example = _build_serializer_example(field.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if isinstance(field, serializers.ListField):
        child_example = _build_field_example(field_name, field.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if isinstance(field, serializers.DictField):
        return {"key": "value"}
    if isinstance(field, serializers.SerializerMethodField):
        return _string_example(field_name)
    if isinstance(field, serializers.BaseSerializer):
        return _build_serializer_example(field, include_read_only=include_read_only)
    if isinstance(field, serializers.BooleanField):
        return True
    if isinstance(field, (serializers.IntegerField, serializers.PrimaryKeyRelatedField)):
        return FIELD_NAME_EXAMPLES.get(field_name, 1)
    if isinstance(field, serializers.FloatField):
        return 1.5
    if isinstance(field, serializers.DecimalField):
        return "1000.00"
    if isinstance(field, serializers.DateTimeField):
        return "2026-02-26T10:30:00Z"
    if isinstance(field, serializers.DateField):
        return "2026-02-26"
    if isinstance(field, serializers.TimeField):
        return "10:30:00"
    if isinstance(field, serializers.EmailField):
        return "officer@example.com"
    if isinstance(field, serializers.URLField):
        return "https://example.com/resource"
    if isinstance(field, serializers.UUIDField):
        return "123e4567-e89b-12d3-a456-426614174000"
    if isinstance(field, serializers.JSONField):
        return {"key": "value"}
    if isinstance(field, serializers.CharField):
        return _string_example(field_name)
    return _string_example(field_name)


def _build_serializer_example(serializer_like, *, include_read_only):
    serializer_like = _instantiate_serializer(serializer_like)
    if serializer_like is None:
        return None
    if serializer_like == OpenApiTypes.STR:
        return "example"
    if isinstance(serializer_like, serializers.ListSerializer):
        child_example = _build_serializer_example(serializer_like.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if not isinstance(serializer_like, serializers.BaseSerializer):
        return None
    if not hasattr(serializer_like, "fields"):
        return None

    example = {}
    for field_name, field in serializer_like.fields.items():
        if include_read_only and getattr(field, "write_only", False):
            continue
        if not include_read_only and getattr(field, "read_only", False):
            continue
        value = _build_field_example(field_name, field, include_read_only=include_read_only)
        if value is not None:
            example[field_name] = value
    return example or None


def _pick_success_response_serializer(response_serializers):
    if isinstance(response_serializers, Mapping):
        for code in ("200", 200, "201", 201, "202", 202):
            if code in response_serializers:
                return response_serializers[code]
        for code, serializer_like in response_serializers.items():
            if str(code).startswith("2"):
                return serializer_like
        return next(iter(response_serializers.values()), None)
    return response_serializers


class PoliceAutoSchema(AutoSchema):
    def _allows_anonymous(self):
        permission_classes = getattr(self.view, "permission_classes", None) or api_settings.DEFAULT_PERMISSION_CLASSES
        for permission_class in permission_classes:
            if inspect.isclass(permission_class) and issubclass(permission_class, AllowAny):
                return True
        return False

    def get_description(self):
        base_description = super().get_description() or ""
        handler = getattr(self.view, self.method.lower(), None)
        doc_description = inspect.getdoc(handler) or inspect.getdoc(self.view) or ""

        description_parts = []
        if base_description.strip():
            description_parts.append(base_description.strip())
        elif doc_description.strip():
            description_parts.append(doc_description.strip())

        auth_text = "Authentication: No JWT required." if self._allows_anonymous() else "Authentication: Bearer JWT access token required."
        description_parts.append(auth_text)

        roles = getattr(self.view, "required_roles", None)
        if roles:
            description_parts.append(f"Required roles: {', '.join(roles)}")

        description_parts.append("Errors use the envelope `{error: {code, message, details}}`.")
        return "\n\n".join(description_parts)

    def get_examples(self):
        examples = list(super().get_examples() or [])
        has_request = any(getattr(example, "request_only", False) for example in examples)
        has_response = any(getattr(example, "response_only", False) for example in examples)

        if not has_request:
            request_example = _build_serializer_example(self.get_request_serializer(), include_read_only=False)
            if request_example is not None:
                examples.append(OpenApiExample("Request Example", value=request_example, request_only=True))

        if not has_response:
            response_serializer = _pick_success_response_serializer(self.get_response_serializers())
            response_example = _build_serializer_example(response_serializer, include_read_only=True)
            if response_example is not None:
                examples.append(OpenApiExample("Success Response", value=response_example, response_only=True))

        if not any(getattr(example, "response_only", False) and example.name == GENERIC_ERROR_EXAMPLE.name for example in examples):
            examples.append(GENERIC_ERROR_EXAMPLE)
        return examples
