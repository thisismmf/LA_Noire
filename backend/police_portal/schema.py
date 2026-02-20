from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiExample


GENERIC_REQUEST_EXAMPLE = OpenApiExample(
    "Request Example",
    value={"example": "value"},
    request_only=True,
)

GENERIC_SUCCESS_EXAMPLE = OpenApiExample(
    "Success Response",
    value={"success": True},
    response_only=True,
)

GENERIC_ERROR_EXAMPLE = OpenApiExample(
    "Error Response",
    value={
        "error": {
            "code": "validation_error",
            "message": "Readable message",
            "details": {"field": ["..."]},
        }
    },
    response_only=True,
)


class PoliceAutoSchema(AutoSchema):
    def get_description(self):
        description = super().get_description() or ""
        roles = getattr(self.view, "required_roles", None)
        if roles:
            role_text = ", ".join(roles)
            description = f"{description}\n\nRequired roles: {role_text}"
        return description

    def get_examples(self):
        examples = super().get_examples() or []
        has_request = any(getattr(example, "request_only", False) for example in examples)
        has_response = any(getattr(example, "response_only", False) for example in examples)
        if not has_request:
            examples.append(GENERIC_REQUEST_EXAMPLE)
        if not has_response:
            examples.append(GENERIC_SUCCESS_EXAMPLE)
            examples.append(GENERIC_ERROR_EXAMPLE)
        return examples
