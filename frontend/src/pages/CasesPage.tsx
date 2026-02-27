import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Case, Complaint } from "../api/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../features/auth/authStore";
import { extractApiError } from "../utils/errors";
import { formatDate, toTitleCase } from "../utils/format";
import {
  addComplainant,
  approveCrimeSceneCase,
  cadetReviewComplaint,
  createCaseAssignment,
  createComplaint,
  createCrimeSceneCase,
  deleteCaseAssignment,
  listCaseAssignments,
  listCases,
  listComplaintQueue,
  officerReviewComplaint,
  resubmitComplaint,
  reviewComplainant,
  updateCaseStatus,
} from "./casesApi";

type ComplaintFormState = {
  title: string;
  description: string;
  crime_level: number;
  location: string;
  incident_datetime: string;
  complainant_name: string;
  complainant_phone: string;
  complainant_national_id: string;
};

const emptyComplaint: ComplaintFormState = {
  title: "",
  description: "",
  crime_level: 1,
  location: "",
  incident_datetime: "",
  complainant_name: "",
  complainant_phone: "",
  complainant_national_id: "",
};

const emptyCrimeScene = {
  title: "",
  description: "",
  crime_level: 1,
  location: "",
  incident_datetime: "",
  scene_datetime: "",
  witness_name: "",
  witness_phone: "",
  witness_national_id: "",
};

function levelOptions() {
  return (
    <>
      <option value={1}>Level 3</option>
      <option value={2}>Level 2</option>
      <option value={3}>Level 1</option>
      <option value={4}>Critical</option>
    </>
  );
}

export function CasesPage() {
  const queryClient = useQueryClient();
  const roles = useAuthStore((state) => state.roles);
  const canReviewQueue = roles.some((role) => ["cadet", "police-officer", "patrol-officer", "system-administrator"].includes(role));
  const canCreateCrimeScene = roles.some((role) =>
    ["police-officer", "patrol-officer", "detective", "sergeant", "captain", "police-chief", "system-administrator"].includes(role),
  );
  const canManageAssignments = roles.some((role) => ["sergeant", "captain", "police-chief", "system-administrator"].includes(role));
  const canCadet = roles.includes("cadet");
  const canOfficer = roles.some((role) => ["police-officer", "patrol-officer"].includes(role));

  const [complaintForm, setComplaintForm] = useState(emptyComplaint);
  const [crimeSceneForm, setCrimeSceneForm] = useState(emptyCrimeScene);
  const [resubmitId, setResubmitId] = useState<number>(0);
  const [selectedCaseId, setSelectedCaseId] = useState<number>(0);
  const [assignForm, setAssignForm] = useState<{ user_id: number; role_in_case: "detective" | "officer" | "sergeant" }>({
    user_id: 0,
    role_in_case: "detective",
  });
  const [reviewMessageMap, setReviewMessageMap] = useState<Record<number, string>>({});
  const [officerSelectionMap, setOfficerSelectionMap] = useState<Record<number, number>>({});
  const [pageMessage, setPageMessage] = useState("");

  const casesQuery = useQuery({
    queryKey: ["cases"],
    queryFn: listCases,
  });

  const queueQuery = useQuery({
    queryKey: ["complaint-queue"],
    queryFn: listComplaintQueue,
    enabled: canReviewQueue,
  });

  const assignmentsQuery = useQuery({
    queryKey: ["case-assignments", selectedCaseId],
    queryFn: () => listCaseAssignments(selectedCaseId),
    enabled: canManageAssignments && selectedCaseId > 0,
  });

  const createComplaintMutation = useMutation({
    mutationFn: createComplaint,
    onSuccess: () => {
      setPageMessage("Complaint submitted and sent to cadet queue.");
      setComplaintForm(emptyComplaint);
      queryClient.invalidateQueries({ queryKey: ["complaint-queue"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const createCrimeSceneMutation = useMutation({
    mutationFn: createCrimeSceneCase,
    onSuccess: () => {
      setPageMessage("Crime scene case created.");
      setCrimeSceneForm(emptyCrimeScene);
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const resubmitMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ComplaintFormState> }) =>
      resubmitComplaint(id, {
        title: payload.title || undefined,
        description: payload.description || undefined,
        crime_level: payload.crime_level || undefined,
        location: payload.location || undefined,
        incident_datetime: payload.incident_datetime || undefined,
      }),
    onSuccess: () => {
      setPageMessage("Complaint resubmitted.");
      queryClient.invalidateQueries({ queryKey: ["complaint-queue"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const cadetReviewMutation = useMutation({
    mutationFn: ({
      complaintId,
      action,
      message,
      officerId,
    }: {
      complaintId: number;
      action: "approve" | "return";
      message?: string;
      officerId?: number;
    }) =>
      cadetReviewComplaint(complaintId, { action, message, officer_id: officerId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complaint-queue"] });
      setPageMessage("Cadet review submitted.");
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const officerReviewMutation = useMutation({
    mutationFn: ({ complaintId, action, message }: { complaintId: number; action: "approve" | "return_to_cadet"; message?: string }) =>
      officerReviewComplaint(complaintId, { action, message }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complaint-queue"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      setPageMessage("Officer review submitted.");
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const setStatusMutation = useMutation({
    mutationFn: ({ caseId, status }: { caseId: number; status: Case["status"] }) => updateCaseStatus(caseId, { status }),
    onSuccess: () => {
      setPageMessage("Case status updated.");
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const approveCrimeSceneMutation = useMutation({
    mutationFn: ({ caseId, approve }: { caseId: number; approve: boolean }) => approveCrimeSceneCase(caseId, approve),
    onSuccess: () => {
      setPageMessage("Crime scene approval action recorded.");
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const addComplainantMutation = useMutation({
    mutationFn: ({ caseId, full_name, phone, national_id }: { caseId: number; full_name: string; phone: string; national_id: string }) =>
      addComplainant(caseId, { full_name, phone, national_id }),
    onSuccess: () => {
      setPageMessage("Complainant added to case.");
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const reviewComplainantMutation = useMutation({
    mutationFn: ({ complainantId, action, message }: { complainantId: number; action: "approve" | "reject"; message?: string }) =>
      reviewComplainant(complainantId, { action, message }),
    onSuccess: () => {
      setPageMessage("Complainant review saved.");
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["complaint-queue"] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const createAssignmentMutation = useMutation({
    mutationFn: ({ caseId, user_id, role_in_case }: { caseId: number; user_id: number; role_in_case: "detective" | "officer" | "sergeant" }) =>
      createCaseAssignment(caseId, { user_id, role_in_case }),
    onSuccess: () => {
      setPageMessage("Case assignment saved.");
      queryClient.invalidateQueries({ queryKey: ["case-assignments", selectedCaseId] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const deleteAssignmentMutation = useMutation({
    mutationFn: ({ caseId, assignmentId }: { caseId: number; assignmentId: number }) => deleteCaseAssignment(caseId, assignmentId),
    onSuccess: () => {
      setPageMessage("Case assignment removed.");
      queryClient.invalidateQueries({ queryKey: ["case-assignments", selectedCaseId] });
    },
    onError: (error) => setPageMessage(extractApiError(error)),
  });

  const queueData = useMemo(() => queueQuery.data || [], [queueQuery.data]);
  const cases = useMemo(() => casesQuery.data || [], [casesQuery.data]);

  function reviewMessageFor(item: Complaint) {
    return reviewMessageMap[item.id] || "";
  }

  function setReviewMessage(complaintId: number, value: string) {
    setReviewMessageMap((prev) => ({ ...prev, [complaintId]: value }));
  }

  function selectedOfficerFor(complaintId: number) {
    return officerSelectionMap[complaintId] || 0;
  }

  return (
    <section className="page">
      <h1>Case and Complaint Status</h1>
      <p>
        This page supports the full case lifecycle: complaint submissions, cadet and officer approval loops, case status
        transitions, complainant reviews, and assignment operations.
      </p>

      <ErrorAlert message={pageMessage} />

      <div className="cards-grid">
        <Card>
          <h2>Create Complaint Case</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createComplaintMutation.mutate({
                title: complaintForm.title,
                description: complaintForm.description,
                crime_level: complaintForm.crime_level,
                location: complaintForm.location,
                incident_datetime: complaintForm.incident_datetime || undefined,
                complainants: complaintForm.complainant_name
                  ? [
                      {
                        full_name: complaintForm.complainant_name,
                        phone: complaintForm.complainant_phone,
                        national_id: complaintForm.complainant_national_id,
                      },
                    ]
                  : [],
              });
            }}
          >
            <label>
              Title
              <input
                value={complaintForm.title}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, title: event.target.value }))}
                required
              />
            </label>
            <label>
              Description
              <textarea
                value={complaintForm.description}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, description: event.target.value }))}
                required
              />
            </label>
            <label>
              Crime Level
              <select
                value={complaintForm.crime_level}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, crime_level: Number(event.target.value) }))}
              >
                {levelOptions()}
              </select>
            </label>
            <label>
              Location
              <input
                value={complaintForm.location}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, location: event.target.value }))}
                required
              />
            </label>
            <label>
              Incident Datetime
              <input
                type="datetime-local"
                value={complaintForm.incident_datetime}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, incident_datetime: event.target.value }))}
              />
            </label>
            <label>
              Complainant Name
              <input
                value={complaintForm.complainant_name}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, complainant_name: event.target.value }))}
              />
            </label>
            <label>
              Complainant Phone
              <input
                value={complaintForm.complainant_phone}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, complainant_phone: event.target.value }))}
              />
            </label>
            <label>
              Complainant National ID
              <input
                value={complaintForm.complainant_national_id}
                onChange={(event) => setComplaintForm((prev) => ({ ...prev, complainant_national_id: event.target.value }))}
              />
            </label>
            <Button type="submit" disabled={createComplaintMutation.isPending}>
              {createComplaintMutation.isPending ? "Submitting..." : "Submit Complaint"}
            </Button>
          </form>
          <div className="divider" />
          <h3>Resubmit Returned Complaint</h3>
          <div className="inline-form">
            <input
              type="number"
              min={0}
              value={resubmitId}
              onChange={(event) => setResubmitId(Number(event.target.value))}
              placeholder="Complaint ID"
            />
            <Button
              variant="secondary"
              onClick={() =>
                resubmitMutation.mutate({
                  id: resubmitId,
                  payload: {
                    title: complaintForm.title,
                    description: complaintForm.description,
                    location: complaintForm.location,
                    crime_level: complaintForm.crime_level,
                    incident_datetime: complaintForm.incident_datetime,
                  },
                })
              }
              disabled={resubmitMutation.isPending || !resubmitId}
            >
              {resubmitMutation.isPending ? "Resubmitting..." : "Resubmit"}
            </Button>
          </div>
        </Card>

        {canCreateCrimeScene && (
          <Card>
            <h2>Create Crime Scene Case</h2>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault();
                createCrimeSceneMutation.mutate({
                  title: crimeSceneForm.title,
                  description: crimeSceneForm.description,
                  crime_level: crimeSceneForm.crime_level,
                  location: crimeSceneForm.location,
                  incident_datetime: crimeSceneForm.incident_datetime || undefined,
                  scene_datetime: crimeSceneForm.scene_datetime,
                  witnesses:
                    crimeSceneForm.witness_phone || crimeSceneForm.witness_national_id
                      ? [
                          {
                            full_name: crimeSceneForm.witness_name,
                            phone: crimeSceneForm.witness_phone,
                            national_id: crimeSceneForm.witness_national_id,
                          },
                        ]
                      : [],
                });
              }}
            >
              <label>
                Title
                <input
                  value={crimeSceneForm.title}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, title: event.target.value }))}
                  required
                />
              </label>
              <label>
                Description
                <textarea
                  value={crimeSceneForm.description}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, description: event.target.value }))}
                  required
                />
              </label>
              <label>
                Crime Level
                <select
                  value={crimeSceneForm.crime_level}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, crime_level: Number(event.target.value) }))}
                >
                  {levelOptions()}
                </select>
              </label>
              <label>
                Location
                <input
                  value={crimeSceneForm.location}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, location: event.target.value }))}
                  required
                />
              </label>
              <label>
                Scene Datetime
                <input
                  type="datetime-local"
                  value={crimeSceneForm.scene_datetime}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, scene_datetime: event.target.value }))}
                  required
                />
              </label>
              <label>
                Witness Name
                <input
                  value={crimeSceneForm.witness_name}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, witness_name: event.target.value }))}
                />
              </label>
              <label>
                Witness Phone
                <input
                  value={crimeSceneForm.witness_phone}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, witness_phone: event.target.value }))}
                />
              </label>
              <label>
                Witness National ID
                <input
                  value={crimeSceneForm.witness_national_id}
                  onChange={(event) => setCrimeSceneForm((prev) => ({ ...prev, witness_national_id: event.target.value }))}
                />
              </label>
              <Button type="submit" disabled={createCrimeSceneMutation.isPending}>
                {createCrimeSceneMutation.isPending ? "Submitting..." : "Create Crime Scene Case"}
              </Button>
            </form>
          </Card>
        )}
      </div>

      {canReviewQueue && (
        <Card>
          <h2>Complaint Review Queue</h2>
          {queueQuery.isLoading && <Skeleton style={{ height: "4rem" }} />}
          {!queueQuery.isLoading && queueData.length === 0 && (
            <EmptyState title="No Queue Items" description="No complaint is currently waiting for this role's review." />
          )}
          <div className="stack-list">
            {queueData.map((item) => (
              <div key={item.id} className="queue-item">
                <div>
                  <strong>#{item.id}</strong> {item.title}
                  <p className="muted-text">
                    Status: {toTitleCase(item.status)} | Strikes: {item.strike_count} | Last Message: {item.last_message || "-"}
                  </p>
                  <p className="muted-text">
                    Location: {item.location} | Incident: {item.incident_datetime ? formatDate(item.incident_datetime) : "-"}
                  </p>
                  <p>{item.description}</p>
                </div>
                <textarea
                  placeholder="Review message"
                  value={reviewMessageFor(item)}
                  onChange={(event) => setReviewMessage(item.id, event.target.value)}
                />
                <div className="button-row">
                  {canCadet && (
                    <>
                      <input
                        type="number"
                        min={1}
                        placeholder="Officer User ID"
                        value={selectedOfficerFor(item.id) || ""}
                        onChange={(event) =>
                          setOfficerSelectionMap((prev) => ({
                            ...prev,
                            [item.id]: Number(event.target.value),
                          }))
                        }
                      />
                      <Button
                        onClick={() =>
                          cadetReviewMutation.mutate({
                            complaintId: item.id,
                            action: "approve",
                            officerId: selectedOfficerFor(item.id),
                          })
                        }
                        disabled={!selectedOfficerFor(item.id)}
                      >
                        Cadet Approve
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => cadetReviewMutation.mutate({ complaintId: item.id, action: "return", message: reviewMessageFor(item) })}
                      >
                        Return to Complainant
                      </Button>
                    </>
                  )}
                  {canOfficer && (
                    <>
                      <Button onClick={() => officerReviewMutation.mutate({ complaintId: item.id, action: "approve" })}>Officer Approve</Button>
                      <Button
                        variant="secondary"
                        onClick={() =>
                          officerReviewMutation.mutate({
                            complaintId: item.id,
                            action: "return_to_cadet",
                            message: reviewMessageFor(item),
                          })
                        }
                      >
                        Return to Cadet
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <h2>Cases You Can Access</h2>
        {casesQuery.isLoading && <Skeleton style={{ height: "3rem" }} />}
        {!casesQuery.isLoading && cases.length === 0 && (
          <EmptyState title="No Cases" description="You currently do not have any assigned or owned case access." />
        )}
        <div className="stack-list">
          {cases.map((item) => (
            <div key={item.id} className="queue-item">
              <div>
                <strong>
                  #{item.id} {item.title}
                </strong>
                <p className="muted-text">
                  {toTitleCase(item.status)} | {toTitleCase(item.source_type)} | Level {item.crime_level} | Created {formatDate(item.created_at)}
                </p>
              </div>
              <div className="button-row wrap">
                <Button variant="secondary" onClick={() => setStatusMutation.mutate({ caseId: item.id, status: "closed_solved" })}>
                  Close Solved
                </Button>
                <Button variant="secondary" onClick={() => setStatusMutation.mutate({ caseId: item.id, status: "closed_unsolved" })}>
                  Close Unsolved
                </Button>
                <Button variant="danger" onClick={() => setStatusMutation.mutate({ caseId: item.id, status: "voided" })}>
                  Void
                </Button>
                <Button onClick={() => approveCrimeSceneMutation.mutate({ caseId: item.id, approve: true })}>Approve Crime Scene</Button>
                <Button variant="secondary" onClick={() => approveCrimeSceneMutation.mutate({ caseId: item.id, approve: false })}>
                  Reject Crime Scene
                </Button>
              </div>
              {canCadet && (
                <div className="form-grid compact-grid">
                  <h3>Add Complainant</h3>
                  <div className="inline-form">
                    <input placeholder="Full name" id={`complainant-name-${item.id}`} />
                    <input placeholder="Phone" id={`complainant-phone-${item.id}`} />
                    <input placeholder="National ID" id={`complainant-nid-${item.id}`} />
                    <Button
                      onClick={() => {
                        const fullNameInput = document.getElementById(`complainant-name-${item.id}`) as HTMLInputElement | null;
                        const phoneInput = document.getElementById(`complainant-phone-${item.id}`) as HTMLInputElement | null;
                        const nationalIdInput = document.getElementById(`complainant-nid-${item.id}`) as HTMLInputElement | null;
                        if (!fullNameInput || !phoneInput || !nationalIdInput) {
                          return;
                        }
                        addComplainantMutation.mutate({
                          caseId: item.id,
                          full_name: fullNameInput.value,
                          phone: phoneInput.value,
                          national_id: nationalIdInput.value,
                        });
                      }}
                    >
                      Add
                    </Button>
                  </div>
                </div>
              )}
              {canCadet && item.complainants.length > 0 && (
                <div className="stack-list">
                  <h3>Complainants</h3>
                  {item.complainants.map((comp) => (
                    <div key={comp.id} className="queue-item nested">
                      <div>
                        <strong>{comp.full_name}</strong>
                        <p className="muted-text">
                          {toTitleCase(comp.verification_status)} {comp.review_message ? `| ${comp.review_message}` : ""}
                        </p>
                      </div>
                      <div className="button-row">
                        <Button onClick={() => reviewComplainantMutation.mutate({ complainantId: comp.id, action: "approve" })}>Approve</Button>
                        <Button
                          variant="secondary"
                          onClick={() =>
                            reviewComplainantMutation.mutate({
                              complainantId: comp.id,
                              action: "reject",
                              message: reviewMessageMap[comp.id] || "Incomplete complainant information",
                            })
                          }
                        >
                          Reject
                        </Button>
                        <input
                          placeholder="Rejection message"
                          value={reviewMessageMap[comp.id] || ""}
                          onChange={(event) => setReviewMessageMap((prev) => ({ ...prev, [comp.id]: event.target.value }))}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {canManageAssignments && (
        <Card>
          <h2>Case Assignment Management</h2>
          <div className="inline-form">
            <input
              type="number"
              min={0}
              placeholder="Case ID"
              value={selectedCaseId || ""}
              onChange={(event) => setSelectedCaseId(Number(event.target.value))}
            />
            <input
              type="number"
              min={0}
              placeholder="User ID"
              value={assignForm.user_id || ""}
              onChange={(event) => setAssignForm((prev) => ({ ...prev, user_id: Number(event.target.value) }))}
            />
            <select
              value={assignForm.role_in_case}
              onChange={(event) =>
                setAssignForm((prev) => ({ ...prev, role_in_case: event.target.value as "detective" | "officer" | "sergeant" }))
              }
            >
              <option value="detective">Detective</option>
              <option value="officer">Officer</option>
              <option value="sergeant">Sergeant</option>
            </select>
            <Button
              onClick={() => createAssignmentMutation.mutate({ caseId: selectedCaseId, user_id: assignForm.user_id, role_in_case: assignForm.role_in_case })}
              disabled={!selectedCaseId || !assignForm.user_id}
            >
              Save Assignment
            </Button>
          </div>
          {assignmentsQuery.isLoading && selectedCaseId > 0 && <Skeleton style={{ height: "3rem" }} />}
          {assignmentsQuery.data && assignmentsQuery.data.length > 0 && (
            <div className="stack-list">
              {assignmentsQuery.data.map((assignment) => (
                <div key={assignment.id} className="queue-item">
                  <span>
                    User #{assignment.user} as {toTitleCase(assignment.role_in_case)}
                  </span>
                  <Button
                    variant="danger"
                    onClick={() => deleteAssignmentMutation.mutate({ caseId: selectedCaseId, assignmentId: assignment.id })}
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </section>
  );
}
