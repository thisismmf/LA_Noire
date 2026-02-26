import { apiClient } from "../api/client";
import type { Case, CaseAssignment, Complaint } from "../api/types";

export type ComplaintPayload = {
  title: string;
  description: string;
  crime_level: number;
  location: string;
  incident_datetime?: string;
  complainants: {
    full_name: string;
    phone: string;
    national_id: string;
  }[];
};

export type CrimeScenePayload = {
  title: string;
  description: string;
  crime_level: number;
  location: string;
  incident_datetime?: string;
  scene_datetime: string;
  witnesses: {
    full_name: string;
    phone: string;
    national_id: string;
  }[];
};

export async function listCases() {
  const { data } = await apiClient.get<Case[]>("/cases/");
  return data;
}

export async function listComplaintQueue() {
  const { data } = await apiClient.get<Complaint[]>("/cases/complaints/queue/");
  return data;
}

export async function createComplaint(payload: ComplaintPayload) {
  const { data } = await apiClient.post<Complaint>("/cases/complaints/", payload);
  return data;
}

export async function resubmitComplaint(complaintId: number, payload: Partial<ComplaintPayload>) {
  const { data } = await apiClient.post<Complaint>(`/cases/complaints/${complaintId}/resubmit/`, payload);
  return data;
}

export async function cadetReviewComplaint(complaintId: number, payload: { action: "approve" | "return"; message?: string }) {
  const { data } = await apiClient.post<Complaint>(`/cases/complaints/${complaintId}/cadet-review/`, payload);
  return data;
}

export async function officerReviewComplaint(
  complaintId: number,
  payload: { action: "approve" | "return_to_cadet"; message?: string },
) {
  const { data } = await apiClient.post<Complaint>(`/cases/complaints/${complaintId}/officer-review/`, payload);
  return data;
}

export async function createCrimeSceneCase(payload: CrimeScenePayload) {
  const { data } = await apiClient.post<{ case: Case; crime_scene_report_id: number }>("/cases/crime-scene/", payload);
  return data;
}

export async function approveCrimeSceneCase(caseId: number, approve: boolean) {
  const { data } = await apiClient.post<{ case: Case; crime_scene_report_id: number }>(
    `/cases/${caseId}/crime-scene/approve/`,
    { approve },
  );
  return data;
}

export async function updateCaseStatus(caseId: number, payload: Partial<Case>) {
  const { data } = await apiClient.patch<Case>(`/cases/${caseId}/`, payload);
  return data;
}

export async function addComplainant(caseId: number, payload: { full_name: string; phone: string; national_id: string }) {
  const { data } = await apiClient.post<Case>(`/cases/${caseId}/add-complainant/`, payload);
  return data;
}

export async function reviewComplainant(complainantId: number, payload: { action: "approve" | "reject"; message?: string }) {
  const { data } = await apiClient.post(`/cases/complainants/${complainantId}/review/`, payload);
  return data;
}

export async function listCaseAssignments(caseId: number) {
  const { data } = await apiClient.get<CaseAssignment[]>(`/cases/${caseId}/assignments/`);
  return data;
}

export async function createCaseAssignment(caseId: number, payload: { user_id: number; role_in_case: "detective" | "officer" | "sergeant" }) {
  const { data } = await apiClient.post<CaseAssignment>(`/cases/${caseId}/assignments/`, payload);
  return data;
}

export async function deleteCaseAssignment(caseId: number, assignmentId: number) {
  await apiClient.delete(`/cases/${caseId}/assignments/${assignmentId}/`);
}
