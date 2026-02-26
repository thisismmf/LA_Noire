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

export type EvidenceType = "witness_statement" | "medical" | "vehicle" | "identity_document" | "other";

export type Evidence = {
  id: number;
  case: number;
  title: string;
  description: string;
  evidence_type: EvidenceType;
  created_at: string;
  created_by: number | null;
  witness_statement?: {
    transcription: string;
    media: Array<{ id: number; file: string; media_type: string }>;
  };
  medical?: {
    forensic_result: string;
    identity_db_result: string;
    status: string;
    images: Array<{ id: number; image: string }>;
  };
  vehicle?: {
    model: string;
    color: string;
    license_plate: string;
    serial_number: string;
  };
  identity_document?: {
    owner_full_name: string;
    data: Record<string, string>;
  };
};

export type BoardItem = {
  id: number;
  item_type: "EVIDENCE_REF" | "NOTE";
  evidence: number | null;
  title: string;
  text: string;
  x: number;
  y: number;
  updated_at: string;
};

export type BoardConnection = {
  id: number;
  from_item: number;
  to_item: number;
  created_at: string;
};

export type DetectiveBoard = {
  id: number;
  case: number;
  items: BoardItem[];
  connections: BoardConnection[];
  updated_at: string;
};

export type CaseReport = {
  case: Case;
  complaint: {
    id: number;
    status: string;
    strike_count: number;
    last_message: string;
  } | null;
  crime_scene_report: {
    id: number;
    status: string;
    scene_datetime: string;
    reported_by: number | null;
    approved_by: number | null;
    approved_at: string | null;
    witnesses: Array<{
      full_name: string;
      phone: string;
      national_id: string;
    }>;
  } | null;
  reviews: Array<{
    decision: string;
    message: string;
    reviewer: number | null;
    created_at: string;
  }>;
  evidence: Evidence[];
  suspects: Array<Record<string, unknown>>;
  interrogations: Array<Record<string, unknown>>;
  assignments: Array<Record<string, unknown>>;
};

export type TrialDecision = {
  id: number;
  case: number;
  judge: number;
  verdict: "guilty" | "not_guilty";
  punishment_title: string;
  punishment_description: string;
  decided_at: string;
};

export type Role = {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_system: boolean;
};
