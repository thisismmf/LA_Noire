import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../../features/auth/authStore";
import { hasAnyRole } from "../../utils/roles";
import type { RoleSlug } from "../../api/types";

type NavItem = {
  to: string;
  label: string;
  roles?: RoleSlug[];
};

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/cases", label: "Case & Complaint Status" },
  {
    to: "/board",
    label: "Detective Board",
    roles: ["detective", "sergeant", "captain", "police-chief", "system-administrator"],
  },
  { to: "/evidence", label: "Evidence Hub" },
  { to: "/reports", label: "General Reporting", roles: ["judge", "captain", "police-chief", "system-administrator"] },
  { to: "/tips", label: "Reward & Tips" },
  { to: "/payments", label: "Payments", roles: ["sergeant", "system-administrator"] },
  { to: "/admin", label: "Admin Panel", roles: ["system-administrator"] },
];

export function AppLayout() {
  const roles = useAuthStore((state) => state.roles);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>Operations</h2>
        <nav>
          {navItems
            .filter((item) => !item.roles || hasAnyRole(roles, item.roles))
            .map((item) => (
              <NavLink key={item.to} to={item.to}>
                {item.label}
              </NavLink>
            ))}
        </nav>
      </aside>
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  );
}
