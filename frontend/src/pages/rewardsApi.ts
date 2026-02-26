import { apiClient } from "../api/client";
import type { RewardLookupResponse, Tip } from "../api/types";

export async function createTip(payload: { case?: number; person?: number; content: string }) {
  const { data } = await apiClient.post<Tip>("/tips/", payload);
  return data;
}

export async function listMyTips() {
  const { data } = await apiClient.get<Tip[]>("/tips/");
  return data;
}

export async function listTipQueue() {
  const { data } = await apiClient.get<Tip[]>("/tips/review-queue/");
  return data;
}

export async function officerReviewTip(tipId: number, approve: boolean, message?: string) {
  const { data } = await apiClient.post<Tip>(`/tips/${tipId}/officer-review/`, { approve, message: message || "" });
  return data;
}

export async function detectiveReviewTip(tipId: number, approve: boolean, message?: string) {
  const { data } = await apiClient.post<Tip>(`/tips/${tipId}/detective-review/`, { approve, message: message || "" });
  return data;
}

export async function lookupReward(nationalId: string, code: string) {
  const query = new URLSearchParams({
    national_id: nationalId,
    code,
  });
  const { data } = await apiClient.get<RewardLookupResponse>(`/rewards/lookup/?${query.toString()}`);
  return data;
}
