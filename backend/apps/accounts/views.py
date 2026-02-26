from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import RegisterSerializer, LoginSerializer, LoginResponseSerializer, UserSerializer, UserWithRolesSerializer
from .models import User
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_SYSTEM_ADMIN
from apps.rbac.utils import get_user_role_slugs


class RegisterView(generics.CreateAPIView):
    """Create a base user account that can later receive additional roles from a system administrator."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        description=(
            "Authenticate with username, email, phone number, or national ID and return a JWT token pair.\n\n"
            "Authentication: No JWT required.\n\n"
            "Errors use the envelope `{error: {code, message, details}}`."
        ),
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = serializer.get_tokens(user)
        return Response({"tokens": tokens, "user": UserSerializer(user).data}, status=status.HTTP_200_OK)


class TokenRefreshDocsView(TokenRefreshView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer("TokenRefreshRequest", fields={"refresh": serializers.CharField()}),
        responses=inline_serializer("TokenRefreshResponse", fields={"access": serializers.CharField()}),
        description=(
            "Exchange a valid refresh token for a new access token.\n\n"
            "Authentication: No JWT required.\n\n"
            "Errors use the envelope `{error: {code, message, details}}`."
        ),
        examples=[
            OpenApiExample(
                "Refresh Request",
                value={"refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh"},
                request_only=True,
            ),
            OpenApiExample(
                "Refresh Response",
                value={"access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access"},
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    @extend_schema(request=None, responses={200: UserWithRolesSerializer})
    def get(self, request):
        """Return the authenticated user profile together with their resolved role slugs."""

        data = UserSerializer(request.user).data
        data["roles"] = get_user_role_slugs(request.user)
        return Response(data)


class UserListView(APIView):
    """List users for system administrators with optional filters by username, national ID, and role."""

    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(name="username", type=str, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="national_id", type=str, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="role", type=str, required=False, location=OpenApiParameter.QUERY),
        ],
        responses={200: UserWithRolesSerializer(many=True)},
    )
    def get(self, request):
        queryset = User.objects.all().order_by("id")
        username = request.query_params.get("username")
        national_id = request.query_params.get("national_id")
        role_slug = request.query_params.get("role")
        if username:
            queryset = queryset.filter(username__icontains=username)
        if national_id:
            queryset = queryset.filter(national_id__icontains=national_id)
        if role_slug:
            queryset = queryset.filter(user_roles__role__slug=role_slug)
        queryset = queryset.distinct()
        data = []
        for user in queryset:
            row = UserSerializer(user).data
            row["roles"] = get_user_role_slugs(user)
            data.append(row)
        return Response(data, status=status.HTTP_200_OK)
