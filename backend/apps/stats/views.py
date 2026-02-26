from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.cases.models import Case
from apps.cases.constants import CaseStatus
from apps.rbac.utils import get_user_role_slugs
from apps.rbac.constants import (
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
    ROLE_JUDGE,
)
from apps.accounts.models import User


EMPLOYEE_ROLES = {
    ROLE_CADET,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_DETECTIVE,
    ROLE_SERGEANT,
    ROLE_CAPTAIN,
    ROLE_POLICE_CHIEF,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
    ROLE_JUDGE,
}


class StatsOverviewSerializer(serializers.Serializer):
    total_solved_cases = serializers.IntegerField()
    total_employees = serializers.IntegerField()
    active_cases = serializers.IntegerField()


class StatsOverviewView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={200: StatsOverviewSerializer},
        description=(
            "Return public homepage counters for resolved cases, active cases, and organization employees.\n\n"
            "Authentication: No JWT required.\n\n"
            "Errors use the envelope `{error: {code, message, details}}`."
        ),
    )
    def get(self, request):
        total_solved = Case.objects.filter(status=CaseStatus.CLOSED_SOLVED).count()
        active_cases = Case.objects.filter(status__in=[CaseStatus.ACTIVE, CaseStatus.PENDING_SUPERIOR_APPROVAL]).count()
        employees = 0
        for user in User.objects.all():
            roles = set(get_user_role_slugs(user))
            if roles.intersection(EMPLOYEE_ROLES):
                employees += 1
        data = {
            "total_solved_cases": total_solved,
            "total_employees": employees,
            "active_cases": active_cases,
        }
        return Response(data, status=status.HTTP_200_OK)
