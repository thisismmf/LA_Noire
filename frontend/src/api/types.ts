export type RoleSlug =
  | "system-administrator"
  | "police-chief"
  | "captain"
  | "sergeant"
  | "detective"
  | "police-officer"
  | "patrol-officer"
  | "cadet"
  | "complainant"
  | "witness"
  | "suspect"
  | "criminal"
  | "judge"
  | "coroner"
  | "base-user"
  | string;

export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export type User = {
  id: number;
  username: string;
  email: string;
  phone: string;
  national_id: string;
  first_name: string;
  last_name: string;
  roles?: RoleSlug[];
};

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type LoginResponse = {
  tokens: AuthTokens;
  user: User;
};

export type StatsOverview = {
  total_solved_cases: number;
  total_employees: number;
  active_cases: number;
};
