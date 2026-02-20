from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from .models import Role, UserRole
from .serializers import RoleSerializer, AssignRoleSerializer
from .permissions import RoleRequiredPermission
from .constants import ROLE_SYSTEM_ADMIN
from apps.accounts.models import User


class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]


class AssignRoleView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = [ROLE_SYSTEM_ADMIN]

    @extend_schema(request=AssignRoleSerializer, responses={200: RoleSerializer})
    def post(self, request, user_id):
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
