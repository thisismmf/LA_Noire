import type { RoleSlug } from "../api/types";

export function hasAnyRole(userRoles: RoleSlug[], required: RoleSlug[]) {
  return required.some((role) => userRoles.includes(role));
}

export function isEmployee(roles: RoleSlug[]) {
  const employeeRoles: RoleSlug[] = [
    "cadet",
    "police-officer",
    "patrol-officer",
    "detective",
    "sergeant",
    "captain",
    "police-chief",
    "coroner",
    "system-administrator",
    "judge",
  ];
  return hasAnyRole(roles, employeeRoles);
}
