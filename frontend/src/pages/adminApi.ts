import { apiClient } from "../api/client";
import type { Role, User } from "../api/types";

export async function listRoles() {
  const { data } = await apiClient.get<Role[]>("/rbac/roles/");
  return data;
}

export async function createRole(payload: { name: string; slug: string; description: string }) {
  const { data } = await apiClient.post<Role>("/rbac/roles/", payload);
  return data;
}

export async function updateRole(roleId: number, payload: Partial<{ name: string; slug: string; description: string }>) {
  const { data } = await apiClient.patch<Role>(`/rbac/roles/${roleId}/`, payload);
  return data;
}

export async function deleteRole(roleId: number) {
  await apiClient.delete(`/rbac/roles/${roleId}/`);
}

export async function listUsers(query: { username?: string; national_id?: string; role?: string }) {
  const params = new URLSearchParams();
  if (query.username) {
    params.set("username", query.username);
  }
  if (query.national_id) {
    params.set("national_id", query.national_id);
  }
  if (query.role) {
    params.set("role", query.role);
  }
  const queryString = params.toString();
  const { data } = await apiClient.get<User[]>(`/users/${queryString ? `?${queryString}` : ""}`);
  return data;
}

export async function assignRole(userId: number, payload: { role_id?: number; role_slug?: string }) {
  const { data } = await apiClient.post<Role>(`/rbac/users/${userId}/assign-role/`, payload);
  return data;
}

export async function removeRole(userId: number, payload: { role_id?: number; role_slug?: string }) {
  await apiClient.post(`/rbac/users/${userId}/remove-role/`, payload);
}
