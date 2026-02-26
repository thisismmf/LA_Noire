import { apiClient } from "../api/client";
import type { Notification } from "../api/types";

export async function listNotifications() {
  const { data } = await apiClient.get<Notification[]>("/notifications/");
  return data;
}

export async function markNotificationRead(notificationId: number) {
  const { data } = await apiClient.post<Notification>(`/notifications/${notificationId}/read/`);
  return data;
}
