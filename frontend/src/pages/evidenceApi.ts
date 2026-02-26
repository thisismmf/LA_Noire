import { apiClient } from "../api/client";
import type { Evidence, EvidenceType } from "../api/types";

export type EvidenceCreatePayload = {
  evidence_type: EvidenceType;
  title: string;
  description: string;
  witness_statement?: {
    transcription: string;
    media?: Array<{ file: string; media_type: string }>;
  };
  medical?: {
    forensic_result?: string;
    identity_db_result?: string;
    status?: string;
    images?: Array<{ image: string }>;
  };
  vehicle?: {
    model: string;
    color: string;
    license_plate?: string;
    serial_number?: string;
  };
  identity_document?: {
    owner_full_name: string;
    data: Record<string, string>;
  };
};

export async function listCaseEvidence(caseId: number, type?: EvidenceType) {
  const query = type ? `?type=${type}` : "";
  const { data } = await apiClient.get<Evidence[]>(`/cases/${caseId}/evidence/${query}`);
  return data;
}

export async function createEvidence({ caseId, payload }: { caseId: number; payload: EvidenceCreatePayload }) {
  const { data } = await apiClient.post<Evidence>(`/cases/${caseId}/evidence/`, payload);
  return data;
}

export async function patchEvidence(evidenceId: number, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch<Evidence>(`/evidence/${evidenceId}/`, payload);
  return data;
}

export async function deleteEvidence(evidenceId: number) {
  await apiClient.delete(`/evidence/${evidenceId}/`);
}
