import { apiClient } from "../api/client";
import type { Payment, PaymentCreateResponse } from "../api/types";

export async function createPayment(payload: { case_id: number; person_id: number; amount: number; type: "bail" | "fine" }) {
  const { data } = await apiClient.post<PaymentCreateResponse>("/payments/create/", payload);
  return data;
}

export async function submitPaymentCallback(payload: { payment_id: number; status: "success" | "failed"; signature: string }) {
  const { data } = await apiClient.post<Payment>("/payments/callback/", payload);
  return data;
}
