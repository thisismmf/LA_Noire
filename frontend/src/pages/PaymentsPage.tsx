import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { formatDate, formatMoney, toTitleCase } from "../utils/format";
import { createPayment, submitPaymentCallback } from "./paymentsApi";
import { extractApiError } from "../utils/errors";

export function PaymentsPage() {
  const [paymentForm, setPaymentForm] = useState({
    case_id: "",
    person_id: "",
    amount: "",
    type: "bail" as "bail" | "fine",
  });
  const [message, setMessage] = useState("");

  const createMutation = useMutation({
    mutationFn: createPayment,
    onError: (error) => setMessage(extractApiError(error)),
  });

  const callbackMutation = useMutation({
    mutationFn: submitPaymentCallback,
    onError: (error) => setMessage(extractApiError(error)),
  });

  return (
    <section className="page">
      <h1>Bail and Fine Payments</h1>
      <p>Create payment links for eligible cases and simulate gateway callback verification.</p>
      <ErrorAlert message={message} />

      <div className="cards-grid">
        <Card>
          <h2>Create Payment</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createMutation.mutate({
                case_id: Number(paymentForm.case_id),
                person_id: Number(paymentForm.person_id),
                amount: Number(paymentForm.amount),
                type: paymentForm.type,
              });
            }}
          >
            <label>
              Case ID
              <input value={paymentForm.case_id} onChange={(event) => setPaymentForm((prev) => ({ ...prev, case_id: event.target.value }))} required />
            </label>
            <label>
              Person ID
              <input
                value={paymentForm.person_id}
                onChange={(event) => setPaymentForm((prev) => ({ ...prev, person_id: event.target.value }))}
                required
              />
            </label>
            <label>
              Amount (Rials)
              <input value={paymentForm.amount} onChange={(event) => setPaymentForm((prev) => ({ ...prev, amount: event.target.value }))} required />
            </label>
            <label>
              Type
              <select
                value={paymentForm.type}
                onChange={(event) => setPaymentForm((prev) => ({ ...prev, type: event.target.value as "bail" | "fine" }))}
              >
                <option value="bail">Bail</option>
                <option value="fine">Fine</option>
              </select>
            </label>
            <Button type="submit" disabled={createMutation.isPending}>
              Create Payment
            </Button>
          </form>
        </Card>

        {createMutation.data && (
          <Card>
            <h2>Gateway Data</h2>
            <p>
              <strong>Payment ID:</strong> {createMutation.data.payment.id}
            </p>
            <p>
              <strong>Status:</strong> {toTitleCase(createMutation.data.payment.status)}
            </p>
            <p>
              <strong>Amount:</strong> {formatMoney(createMutation.data.payment.amount)}
            </p>
            <p>
              <strong>Redirect URL:</strong> {createMutation.data.redirect_url}
            </p>
            <p>
              <strong>Signature:</strong> {createMutation.data.signature}
            </p>
            <div className="button-row">
              <Button
                onClick={() =>
                  callbackMutation.mutate({
                    payment_id: createMutation.data!.payment.id,
                    status: "success",
                    signature: createMutation.data!.signature,
                  })
                }
              >
                Simulate Success
              </Button>
              <Button
                variant="danger"
                onClick={() =>
                  callbackMutation.mutate({
                    payment_id: createMutation.data!.payment.id,
                    status: "failed",
                    signature: createMutation.data!.signature,
                  })
                }
              >
                Simulate Failure
              </Button>
            </div>
            {callbackMutation.data && (
              <div className="queue-item">
                <p>
                  Callback status: <strong>{toTitleCase(callbackMutation.data.status)}</strong>
                </p>
                <p>Verified at: {formatDate(callbackMutation.data.verified_at)}</p>
                <p>Gateway ref: {callbackMutation.data.gateway_ref}</p>
              </div>
            )}
          </Card>
        )}
      </div>
    </section>
  );
}
