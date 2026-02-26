import { Bell, LogOut, ShieldUser } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useAuthStore } from "../../features/auth/authStore";

export function TopNav() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const user = useAuthStore((state) => state.user);

  return (
    <header className="top-nav">
      <div className="brand-row">
        <Link to="/" className="brand-link">
          LA Noire Police Portal
        </Link>
      </div>

      <nav className="main-nav-links">
        <NavLink to="/">Home</NavLink>
        <NavLink to="/most-wanted">Most Wanted</NavLink>
        {user ? <NavLink to="/dashboard">Dashboard</NavLink> : <NavLink to="/auth">Login</NavLink>}
      </nav>

      <div className="top-nav-actions">
        {user && (
          <>
            <NavLink to="/notifications" className="icon-action" aria-label="Notifications">
              <Bell size={18} />
            </NavLink>
            <div className="user-chip">
              <ShieldUser size={16} />
              <span>{user.username}</span>
            </div>
            <button type="button" className="link-button" onClick={clearAuth}>
              <LogOut size={16} />
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
}
