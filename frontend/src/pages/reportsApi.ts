import { apiClient } from "../api/client";
import type { CaseReport, TrialDecision } from "../api/types";

export async function fetchCaseReport(caseId: number) {
  const { data } = await apiClient.get<CaseReport>(`/cases/${caseId}/report/`);
  return data;
}

export async function submitTrialDecision(
  caseId: number,
  payload: { verdict: "guilty" | "not_guilty"; punishment_title?: string; punishment_description?: string },
) {
  const { data } = await apiClient.post<TrialDecision>(`/cases/${caseId}/trial/decision/`, payload);
  return data;
}
