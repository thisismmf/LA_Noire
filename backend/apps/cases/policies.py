from apps.rbac.utils import get_user_role_slugs
from apps.rbac.constants import (
    ROLE_POLICE_CHIEF,
    ROLE_CAPTAIN,
    ROLE_SERGEANT,
    ROLE_DETECTIVE,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CORONER,
    ROLE_SYSTEM_ADMIN,
)

ROLE_PRIORITY = [
    ROLE_POLICE_CHIEF,
    ROLE_CAPTAIN,
    ROLE_SERGEANT,
    ROLE_DETECTIVE,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CORONER,
]

APPROVAL_MAP = {
    ROLE_PATROL_OFFICER: ROLE_POLICE_OFFICER,
    ROLE_POLICE_OFFICER: ROLE_SERGEANT,
    ROLE_DETECTIVE: ROLE_SERGEANT,
    ROLE_SERGEANT: ROLE_CAPTAIN,
    ROLE_CAPTAIN: ROLE_POLICE_CHIEF,
    ROLE_CORONER: ROLE_CAPTAIN,
}

POLICE_ROLES = set(ROLE_PRIORITY)


def get_primary_role(user):
    role_slugs = get_user_role_slugs(user)
    for role in ROLE_PRIORITY:
        if role in role_slugs:
            return role
    return None


def get_required_approver_role_slug(user):
    primary = get_primary_role(user)
    if not primary:
        return None
    return APPROVAL_MAP.get(primary)


def is_user_assigned_to_case(user, case, role_in_case=None):
    if not user or not user.is_authenticated or not case:
        return False
    from .models import CaseAssignment

    queryset = CaseAssignment.objects.filter(case=case, user=user)
    if role_in_case:
        queryset = queryset.filter(role_in_case=role_in_case)
    return queryset.exists()


def can_user_access_case(user, case):
    if not user or not user.is_authenticated or not case:
        return False
    if user.is_superuser:
        return True
    role_slugs = set(get_user_role_slugs(user))
    if ROLE_SYSTEM_ADMIN in role_slugs:
        return True
    if case.created_by_id == user.id:
        return True
    if case.complaint_id and case.complaint and case.complaint.created_by_id == user.id:
        return True
    return is_user_assigned_to_case(user, case)
