import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { EvidenceType } from "../api/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { formatDate, toTitleCase } from "../utils/format";
import { listCases } from "./casesApi";
import { createEvidence, deleteEvidence, listCaseEvidence, patchEvidence } from "./evidenceApi";

type EvidenceFormState = {
  type: EvidenceType;
  title: string;
  description: string;
  witness_transcription: string;
  medical_forensic_result: string;
  medical_identity_db_result: string;
  medical_status: string;
  medical_image_url: string;
  vehicle_model: string;
  vehicle_color: string;
  vehicle_license_plate: string;
  vehicle_serial_number: string;
  id_owner_name: string;
  id_data_json: string;
};

const emptyForm: EvidenceFormState = {
  type: "other",
  title: "",
  description: "",
  witness_transcription: "",
  medical_forensic_result: "",
  medical_identity_db_result: "",
  medical_status: "pending",
  medical_image_url: "",
  vehicle_model: "",
  vehicle_color: "",
  vehicle_license_plate: "",
  vehicle_serial_number: "",
  id_owner_name: "",
  id_data_json: "{}",
};

export function EvidencePage() {
  const queryClient = useQueryClient();
  const [selectedCaseId, setSelectedCaseId] = useState<number>(0);
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<EvidenceType | "all">("all");
  const [form, setForm] = useState<EvidenceFormState>(emptyForm);
  const [message, setMessage] = useState("");

  const casesQuery = useQuery({
    queryKey: ["cases"],
    queryFn: listCases,
  });

  const evidenceQuery = useQuery({
    queryKey: ["case-evidence", selectedCaseId, selectedTypeFilter],
    queryFn: () => listCaseEvidence(selectedCaseId, selectedTypeFilter === "all" ? undefined : selectedTypeFilter),
    enabled: selectedCaseId > 0,
  });

  const createMutation = useMutation({
    mutationFn: createEvidence,
    onSuccess: () => {
      setMessage("Evidence item created.");
      setForm(emptyForm);
      queryClient.invalidateQueries({ queryKey: ["case-evidence", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const patchMutation = useMutation({
    mutationFn: ({ evidenceId, payload }: { evidenceId: number; payload: Record<string, unknown> }) => patchEvidence(evidenceId, payload),
    onSuccess: () => {
      setMessage("Evidence updated.");
      queryClient.invalidateQueries({ queryKey: ["case-evidence", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteEvidence,
    onSuccess: () => {
      setMessage("Evidence removed.");
      queryClient.invalidateQueries({ queryKey: ["case-evidence", selectedCaseId] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const evidenceData = useMemo(() => evidenceQuery.data || [], [evidenceQuery.data]);

  function submitCreateForm() {
    if (!selectedCaseId) {
      setMessage("Select a case first.");
      return;
    }

    const basePayload = {
      evidence_type: form.type,
      title: form.title,
      description: form.description,
    } as const;

    try {
      if (form.type === "witness_statement") {
        createMutation.mutate({
          caseId: selectedCaseId,
          payload: {
            ...basePayload,
            witness_statement: {
              transcription: form.witness_transcription,
            },
          },
        });
        return;
      }

      if (form.type === "medical") {
        createMutation.mutate({
          caseId: selectedCaseId,
          payload: {
            ...basePayload,
            medical: {
              forensic_result: form.medical_forensic_result,
              identity_db_result: form.medical_identity_db_result,
              status: form.medical_status,
              images: form.medical_image_url ? [{ image: form.medical_image_url }] : [],
            },
          },
        });
        return;
      }

      if (form.type === "vehicle") {
        createMutation.mutate({
          caseId: selectedCaseId,
          payload: {
            ...basePayload,
            vehicle: {
              model: form.vehicle_model,
              color: form.vehicle_color,
              license_plate: form.vehicle_license_plate || undefined,
              serial_number: form.vehicle_serial_number || undefined,
            },
          },
        });
        return;
      }

      if (form.type === "identity_document") {
        createMutation.mutate({
          caseId: selectedCaseId,
          payload: {
            ...basePayload,
            identity_document: {
              owner_full_name: form.id_owner_name,
              data: JSON.parse(form.id_data_json),
            },
          },
        });
        return;
      }

      createMutation.mutate({
        caseId: selectedCaseId,
        payload: basePayload,
      });
    } catch {
      setMessage("Identity document JSON must be valid.");
    }
  }

  return (
    <section className="page">
      <h1>Evidence Registration and Review</h1>
      <p>
        Register and update witness statements, medical evidence, vehicle evidence, identity documents, and simple evidence
        records.
      </p>
      <ErrorAlert message={message} />

      <Card>
        <h2>Evidence Filters</h2>
        <div className="inline-form">
          <select value={selectedCaseId || ""} onChange={(event) => setSelectedCaseId(Number(event.target.value))}>
            <option value="">Select Case</option>
            {casesQuery.data?.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} - {item.title}
              </option>
            ))}
          </select>
          <select value={selectedTypeFilter} onChange={(event) => setSelectedTypeFilter(event.target.value as EvidenceType | "all")}>
            <option value="all">All Types</option>
            <option value="witness_statement">Witness Statement</option>
            <option value="medical">Medical</option>
            <option value="vehicle">Vehicle</option>
            <option value="identity_document">Identity Document</option>
            <option value="other">Other</option>
          </select>
        </div>
      </Card>

      <Card>
        <h2>Create Evidence</h2>
        <form
          className="form-grid"
          onSubmit={(event) => {
            event.preventDefault();
            submitCreateForm();
          }}
        >
          <label>
            Type
            <select value={form.type} onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value as EvidenceType }))}>
              <option value="witness_statement">Witness Statement</option>
              <option value="medical">Medical</option>
              <option value="vehicle">Vehicle</option>
              <option value="identity_document">Identity Document</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>
            Title
            <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} required />
          </label>
          <label>
            Description
            <textarea
              value={form.description}
              onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
              required
            />
          </label>

          {form.type === "witness_statement" && (
            <label>
              Transcription
              <textarea
                value={form.witness_transcription}
                onChange={(event) => setForm((prev) => ({ ...prev, witness_transcription: event.target.value }))}
                required
              />
            </label>
          )}

          {form.type === "medical" && (
            <>
              <label>
                Forensic Result
                <textarea
                  value={form.medical_forensic_result}
                  onChange={(event) => setForm((prev) => ({ ...prev, medical_forensic_result: event.target.value }))}
                />
              </label>
              <label>
                Identity DB Result
                <textarea
                  value={form.medical_identity_db_result}
                  onChange={(event) => setForm((prev) => ({ ...prev, medical_identity_db_result: event.target.value }))}
                />
              </label>
              <label>
                Status
                <input value={form.medical_status} onChange={(event) => setForm((prev) => ({ ...prev, medical_status: event.target.value }))} />
              </label>
              <label>
                Medical Image URL (required by backend)
                <input
                  value={form.medical_image_url}
                  onChange={(event) => setForm((prev) => ({ ...prev, medical_image_url: event.target.value }))}
                  required
                />
              </label>
            </>
          )}

          {form.type === "vehicle" && (
            <>
              <label>
                Model
                <input value={form.vehicle_model} onChange={(event) => setForm((prev) => ({ ...prev, vehicle_model: event.target.value }))} required />
              </label>
              <label>
                Color
                <input value={form.vehicle_color} onChange={(event) => setForm((prev) => ({ ...prev, vehicle_color: event.target.value }))} required />
              </label>
              <label>
                License Plate
                <input
                  value={form.vehicle_license_plate}
                  onChange={(event) => setForm((prev) => ({ ...prev, vehicle_license_plate: event.target.value }))}
                />
              </label>
              <label>
                Serial Number
                <input
                  value={form.vehicle_serial_number}
                  onChange={(event) => setForm((prev) => ({ ...prev, vehicle_serial_number: event.target.value }))}
                />
              </label>
            </>
          )}

          {form.type === "identity_document" && (
            <>
              <label>
                Owner Full Name
                <input value={form.id_owner_name} onChange={(event) => setForm((prev) => ({ ...prev, id_owner_name: event.target.value }))} required />
              </label>
              <label>
                Data JSON
                <textarea value={form.id_data_json} onChange={(event) => setForm((prev) => ({ ...prev, id_data_json: event.target.value }))} />
              </label>
            </>
          )}

          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Submitting..." : "Create Evidence"}
          </Button>
        </form>
      </Card>

      <Card>
        <h2>Evidence List</h2>
        {selectedCaseId === 0 && <EmptyState title="No Case Selected" description="Choose a case to view evidence records." />}
        {selectedCaseId > 0 && evidenceQuery.isLoading && <Skeleton style={{ height: "3rem" }} />}
        {selectedCaseId > 0 && !evidenceQuery.isLoading && evidenceData.length === 0 && (
          <EmptyState title="No Evidence" description="No evidence items match current filters." />
        )}
        <div className="stack-list">
          {evidenceData.map((item) => (
            <div key={item.id} className="queue-item">
              <div>
                <strong>
                  #{item.id} {item.title}
                </strong>
                <p className="muted-text">
                  {toTitleCase(item.evidence_type)} | Created {formatDate(item.created_at)}
                </p>
                <p>{item.description}</p>
                {item.witness_statement && <p>Transcription: {item.witness_statement.transcription}</p>}
                {item.medical && (
                  <p>
                    Medical Status: {item.medical.status} | Forensic: {item.medical.forensic_result || "-"} | Identity DB:{" "}
                    {item.medical.identity_db_result || "-"}
                  </p>
                )}
                {item.vehicle && (
                  <p>
                    Vehicle: {item.vehicle.model} / {item.vehicle.color} / Plate: {item.vehicle.license_plate || "-"} / Serial:{" "}
                    {item.vehicle.serial_number || "-"}
                  </p>
                )}
                {item.identity_document && (
                  <p>
                    Document Owner: {item.identity_document.owner_full_name} | Data: {JSON.stringify(item.identity_document.data)}
                  </p>
                )}
              </div>
              <div className="button-row wrap">
                <Button
                  variant="secondary"
                  onClick={() =>
                    patchMutation.mutate({
                      evidenceId: item.id,
                      payload: {
                        title: `${item.title} (updated)`,
                      },
                    })
                  }
                >
                  Quick Rename
                </Button>
                {item.evidence_type === "medical" && (
                  <>
                    <Button
                      variant="secondary"
                      onClick={() =>
                        patchMutation.mutate({
                          evidenceId: item.id,
                          payload: {
                            forensic_result: "Reviewed by coroner",
                            status: "approved",
                          },
                        })
                      }
                    >
                      Update Coroner Fields
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() =>
                        patchMutation.mutate({
                          evidenceId: item.id,
                          payload: {
                            identity_db_result: "Matched in identity database",
                          },
                        })
                      }
                    >
                      Update Identity DB Result
                    </Button>
                  </>
                )}
                <Button variant="danger" onClick={() => deleteMutation.mutate(item.id)} disabled={deleteMutation.isPending}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
