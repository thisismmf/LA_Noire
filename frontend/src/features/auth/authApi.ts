import { apiClient } from "../../api/client";
import type { LoginResponse, User } from "../../api/types";

export type LoginInput = {
  identifier: string;
  password: string;
};

export type RegisterInput = {
  username: string;
  email: string;
  phone: string;
  national_id: string;
  first_name: string;
  last_name: string;
  password: string;
};

export async function login(input: LoginInput) {
  const { data } = await apiClient.post<LoginResponse>("/auth/login/", input);
  return data;
}

export async function register(input: RegisterInput) {
  const { data } = await apiClient.post<User>("/auth/register/", input);
  return data;
}

export async function fetchMe() {
  const { data } = await apiClient.get<User>("/auth/me/");
  return data;
}
