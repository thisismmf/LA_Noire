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

export type CaseComplainant = {
  id: number;
  full_name: string;
  phone: string;
  national_id: string;
  is_verified: boolean;
  verification_status: "pending" | "approved" | "rejected";
  review_message: string;
};

export type Complaint = {
  id: number;
  title: string;
  description: string;
  crime_level: number;
  location: string;
  incident_datetime: string | null;
  status: string;
  strike_count: number;
  last_message: string;
  complainants: CaseComplainant[];
  created_at: string;
};

export type Case = {
  id: number;
  title: string;
  description: string;
  crime_level: number;
  location: string;
  incident_datetime: string | null;
  status: string;
  source_type: string;
  created_at: string;
  complainants: CaseComplainant[];
};

export type CaseAssignment = {
  id: number;
  case: number;
  user: number;
  role_in_case: "detective" | "officer" | "sergeant";
  assigned_at: string;
};
