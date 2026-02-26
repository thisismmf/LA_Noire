import { useAuthStore } from "../features/auth/authStore";

export function DashboardPage() {
  const roles = useAuthStore((state) => state.roles);

  return (
    <section className="page">
      <h1>Modular Dashboard</h1>
      <p>Role-based modules are shown across the sidebar and pages according to your access level.</p>
      <div className="chip-row">
        {roles.map((role) => (
          <span key={role} className="role-chip">
            {role}
          </span>
        ))}
      </div>
    </section>
  );
}
