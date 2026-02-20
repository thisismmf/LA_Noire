from apps.rbac.utils import get_user_role_slugs
from apps.rbac.constants import (
    ROLE_POLICE_CHIEF,
    ROLE_CAPTAIN,
    ROLE_SERGEANT,
    ROLE_DETECTIVE,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CORONER,
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
