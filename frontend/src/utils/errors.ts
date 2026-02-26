import type { AxiosError } from "axios";
import type { ApiErrorPayload } from "../api/types";

export function extractApiError(error: unknown, fallback = "Request failed") {
  const axiosError = error as AxiosError<ApiErrorPayload>;
  return axiosError.response?.data?.error?.message || fallback;
}
