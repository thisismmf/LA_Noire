import { Navigate, Outlet } from "react-router-dom";
import type { RoleSlug } from "../../api/types";
import { useAuthStore } from "./authStore";
import { hasAnyRole } from "../../utils/roles";

type RoleGuardProps = {
  allowedRoles: RoleSlug[];
};

export function RoleGuard({ allowedRoles }: RoleGuardProps) {
  const roles = useAuthStore((state) => state.roles);
  if (!hasAnyRole(roles, allowedRoles)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Outlet />;
}
