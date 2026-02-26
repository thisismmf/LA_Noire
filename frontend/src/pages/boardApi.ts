import { apiClient } from "../api/client";
import type { BoardConnection, BoardItem, DetectiveBoard } from "../api/types";

export async function fetchBoard(caseId: number) {
  const { data } = await apiClient.get<DetectiveBoard>(`/cases/${caseId}/board/`);
  return data;
}

export async function createBoardItem({ caseId, payload }: { caseId: number; payload: Partial<BoardItem> }) {
  const { data } = await apiClient.post<BoardItem>(`/cases/${caseId}/board/items/`, payload);
  return data;
}

export async function patchBoardItem(itemId: number, payload: Partial<BoardItem>) {
  const { data } = await apiClient.patch<BoardItem>(`/board/items/${itemId}/`, payload);
  return data;
}

export async function deleteBoardItem(itemId: number) {
  await apiClient.delete(`/board/items/${itemId}/`);
}

export async function createBoardConnection(payload: { from_item: number; to_item: number }) {
  const { data } = await apiClient.post<BoardConnection>("/board/connections/", payload);
  return data;
}

export async function deleteBoardConnection(connectionId: number) {
  await apiClient.delete(`/board/connections/${connectionId}/`);
}
