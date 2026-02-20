from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"error": {"code": "server_error", "message": "Internal server error", "details": {}}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_code = "validation_error" if response.status_code == status.HTTP_400_BAD_REQUEST else "error"
    message = "Request failed"
    if isinstance(response.data, dict) and "detail" in response.data:
        message = response.data["detail"]
    response.data = {"error": {"code": error_code, "message": message, "details": response.data}}
    return response
