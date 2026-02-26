from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from .models import Role, UserRole
from .serializers import RoleSerializer, AssignRoleSerializer
from .permissions import RoleRequiredPermission
from .constants import ROLE_SYSTEM_ADMIN, SYSTEM_ROLE_SLUGS
from apps.accounts.models import User


class RoleListCreateView(generics.ListCreateAPIView):
    """List custom and system roles or create a new role without changing source code."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a role while protecting immutable built-in system roles."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]

    def update(self, request, *args, **kwargs):
        role = self.get_object()
        if role.slug in SYSTEM_ROLE_SLUGS:
            return Response(
                {
                    "error": {
                        "code": "forbidden",
                        "message": "System roles are immutable and cannot be modified",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.slug in SYSTEM_ROLE_SLUGS:
            return Response(
                {
                    "error": {
                        "code": "forbidden",
                        "message": "System roles are immutable and cannot be deleted",
                        "details": {},
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class AssignRoleView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]

    @extend_schema(request=AssignRoleSerializer, responses={200: RoleSerializer})
    def post(self, request, user_id):
        """Assign an existing role to a user by role ID or role slug."""

        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.get_role()
        if not role:
            return Response(
                {"error": {"code": "not_found", "message": "Role not found", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        user = get_object_or_404(User, id=user_id)
        UserRole.objects.get_or_create(user=user, role=role, defaults={"assigned_by": request.user})
        return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)


class RemoveRoleView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]

    @extend_schema(request=AssignRoleSerializer, responses={204: None})
    def post(self, request, user_id):
        """Remove an assigned role from a user by role ID or role slug."""

        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.get_role()
        if not role:
            return Response(
                {"error": {"code": "not_found", "message": "Role not found", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        user = get_object_or_404(User, id=user_id)
        UserRole.objects.filter(user=user, role=role).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
