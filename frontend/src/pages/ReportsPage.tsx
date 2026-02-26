import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { formatDate, toTitleCase } from "../utils/format";
import { listCases } from "./casesApi";
import { fetchCaseReport, submitTrialDecision } from "./reportsApi";

export function ReportsPage() {
  const [selectedCaseId, setSelectedCaseId] = useState<number>(0);
  const [verdict, setVerdict] = useState<"guilty" | "not_guilty">("not_guilty");
  const [punishmentTitle, setPunishmentTitle] = useState("");
  const [punishmentDescription, setPunishmentDescription] = useState("");
  const [message, setMessage] = useState("");

  const casesQuery = useQuery({
    queryKey: ["cases"],
    queryFn: listCases,
  });

  const reportQuery = useQuery({
    queryKey: ["case-report", selectedCaseId],
    queryFn: () => fetchCaseReport(selectedCaseId),
    enabled: selectedCaseId > 0,
  });

  const trialMutation = useMutation({
    mutationFn: ({
      caseId,
      payload,
    }: {
      caseId: number;
      payload: { verdict: "guilty" | "not_guilty"; punishment_title?: string; punishment_description?: string };
    }) => submitTrialDecision(caseId, payload),
    onSuccess: () => setMessage("Trial decision submitted."),
    onError: (error) => setMessage(extractApiError(error)),
  });

  const assignmentRows = useMemo(() => reportQuery.data?.assignments || [], [reportQuery.data?.assignments]);

  return (
    <section className="page">
      <h1>General Reporting</h1>
      <p>
        Access full case reports including formation details, evidence, witness statements, approvals, involved police ranks,
        and submit final trial verdict when authorized.
      </p>
      <ErrorAlert message={message} />

      <Card>
        <h2>Report Context</h2>
        <div className="inline-form">
          <select value={selectedCaseId || ""} onChange={(event) => setSelectedCaseId(Number(event.target.value))}>
            <option value="">Select Case</option>
            {casesQuery.data?.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} - {item.title}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {selectedCaseId === 0 && <EmptyState title="No Case Selected" description="Choose a case to load the comprehensive report." />}
      {selectedCaseId > 0 && reportQuery.isLoading && <Skeleton style={{ height: "5rem" }} />}
      {selectedCaseId > 0 && reportQuery.data && (
        <div className="cards-grid">
          <Card>
            <h2>Case Details</h2>
            <p>
              <strong>Title:</strong> {reportQuery.data.case.title}
            </p>
            <p>
              <strong>Status:</strong> {toTitleCase(reportQuery.data.case.status)}
            </p>
            <p>
              <strong>Crime Level:</strong> {reportQuery.data.case.crime_level}
            </p>
            <p>
              <strong>Created:</strong> {formatDate(reportQuery.data.case.created_at)}
            </p>
            <p>
              <strong>Location:</strong> {reportQuery.data.case.location}
            </p>
          </Card>

          <Card>
            <h2>Evidence Summary</h2>
            {reportQuery.data.evidence.length === 0 && <p>No evidence listed.</p>}
            <ul className="flat-list">
              {reportQuery.data.evidence.map((evidence) => (
                <li key={evidence.id}>
                  #{evidence.id} {evidence.title} ({toTitleCase(evidence.evidence_type)})
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <h2>Witness and Review Summary</h2>
            {reportQuery.data.crime_scene_report?.witnesses?.length ? (
              <ul className="flat-list">
                {reportQuery.data.crime_scene_report.witnesses.map((witness) => (
                  <li key={`${witness.national_id}-${witness.phone}`}>
                    {witness.full_name || "Unnamed"} | {witness.phone} | {witness.national_id}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No witness list in this case report.</p>
            )}
            <div className="divider" />
            {reportQuery.data.reviews.length > 0 ? (
              <ul className="flat-list">
                {reportQuery.data.reviews.map((review, index) => (
                  <li key={`${review.created_at}-${index}`}>
                    {toTitleCase(review.decision)} on {formatDate(review.created_at)} | {review.message || "-"}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No complaint review entries.</p>
            )}
          </Card>

          <Card>
            <h2>Assignments and Interrogations</h2>
            {assignmentRows.length === 0 && <p>No assignment rows.</p>}
            <ul className="flat-list">
              {assignmentRows.map((assignment, index) => (
                <li key={`assign-${index}`}>{JSON.stringify(assignment)}</li>
              ))}
            </ul>
            <div className="divider" />
            <p>Interrogation entries: {reportQuery.data.interrogations.length}</p>
            <p>Suspect entries: {reportQuery.data.suspects.length}</p>
          </Card>

          <Card>
            <h2>Trial Decision</h2>
            <form
              className="form-grid"
              onSubmit={(event) => {
                event.preventDefault();
                trialMutation.mutate({
                  caseId: selectedCaseId,
                  payload: {
                    verdict,
                    punishment_title: verdict === "guilty" ? punishmentTitle : "",
                    punishment_description: verdict === "guilty" ? punishmentDescription : "",
                  },
                });
              }}
            >
              <label>
                Verdict
                <select value={verdict} onChange={(event) => setVerdict(event.target.value as "guilty" | "not_guilty")}>
                  <option value="not_guilty">Not Guilty</option>
                  <option value="guilty">Guilty</option>
                </select>
              </label>
              {verdict === "guilty" && (
                <>
                  <label>
                    Punishment Title
                    <input value={punishmentTitle} onChange={(event) => setPunishmentTitle(event.target.value)} required />
                  </label>
                  <label>
                    Punishment Description
                    <textarea value={punishmentDescription} onChange={(event) => setPunishmentDescription(event.target.value)} />
                  </label>
                </>
              )}
              <Button type="submit" disabled={trialMutation.isPending}>
                {trialMutation.isPending ? "Saving..." : "Submit Trial Decision"}
              </Button>
            </form>
          </Card>
        </div>
      )}
    </section>
  );
}
