import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthTokens, RoleSlug, User } from "../../api/types";

type AuthState = {
  user: User | null;
  tokens: AuthTokens | null;
  roles: RoleSlug[];
  isAuthenticated: boolean;
  setAuth: (payload: { user: User; tokens: AuthTokens; roles?: RoleSlug[] }) => void;
  setRoles: (roles: RoleSlug[]) => void;
  clearAuth: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      roles: [],
      isAuthenticated: false,
      setAuth: ({ user, tokens, roles = [] }) =>
        set({
          user,
          tokens,
          roles,
          isAuthenticated: true,
        }),
      setRoles: (roles) => set({ roles }),
      clearAuth: () =>
        set({
          user: null,
          tokens: null,
          roles: [],
          isAuthenticated: false,
        }),
    }),
    {
      name: "la-noire-auth",
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        roles: state.roles,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
