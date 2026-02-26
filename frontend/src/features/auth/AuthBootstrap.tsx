import { useEffect } from "react";
import { fetchMe } from "./authApi";
import { useAuthStore } from "./authStore";

export function AuthBootstrap() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const roles = useAuthStore((state) => state.roles);
  const setAuth = useAuthStore((state) => state.setAuth);
  const setRoles = useAuthStore((state) => state.setRoles);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const user = useAuthStore((state) => state.user);
  const tokens = useAuthStore((state) => state.tokens);

  useEffect(() => {
    if (!isAuthenticated || roles.length > 0 || !tokens || !user) {
      return;
    }
    fetchMe()
      .then((me) => {
        setAuth({ user: me, tokens, roles: me.roles || [] });
        setRoles(me.roles || []);
      })
      .catch(() => clearAuth());
  }, [clearAuth, isAuthenticated, roles.length, setAuth, setRoles, tokens, user]);

  return null;
}
