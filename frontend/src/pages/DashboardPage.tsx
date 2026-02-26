import { Link } from "react-router-dom";
import { Card } from "../components/ui/Card";
import { useAuthStore } from "../features/auth/authStore";
import { allModules } from "../features/dashboard/modules";
import { hasAnyRole } from "../utils/roles";

export function DashboardPage() {
  const roles = useAuthStore((state) => state.roles);
  const user = useAuthStore((state) => state.user);
  const modules = allModules.filter((module) => hasAnyRole(roles, module.roles));

  return (
    <section className="page">
      <h1>Modular Dashboard</h1>
      <p>
        {user?.first_name || user?.username}, your available modules are selected based on current roles and backend access
        policy.
      </p>
      <div className="chip-row">
        {roles.map((role) => (
          <span key={role} className="role-chip">
            {role}
          </span>
        ))}
      </div>
      <div className="cards-grid">
        {modules.map((module) => (
          <Card key={module.id}>
            <h2>{module.title}</h2>
            <p>{module.description}</p>
            <Link to={module.path} className="module-link">
              Open Module
            </Link>
          </Card>
        ))}
      </div>
    </section>
  );
}
