import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../features/auth/authStore";
import { extractApiError } from "../utils/errors";
import { formatDate, formatMoney, toTitleCase } from "../utils/format";
import { createTip, detectiveReviewTip, listMyTips, listTipQueue, lookupReward, officerReviewTip } from "./rewardsApi";

export function TipsRewardsPage() {
  const queryClient = useQueryClient();
  const roles = useAuthStore((state) => state.roles);
  const canReviewAsOfficer = roles.includes("police-officer");
  const canReviewAsDetective = roles.includes("detective");
  const canReviewQueue = canReviewAsOfficer || canReviewAsDetective || roles.includes("system-administrator");
  const canLookupReward = roles.some((role) =>
    ["cadet", "police-officer", "patrol-officer", "detective", "sergeant", "captain", "police-chief", "coroner", "system-administrator"].includes(role),
  );

  const [tipForm, setTipForm] = useState({ case: "", person: "", content: "" });
  const [reviewMessage, setReviewMessage] = useState<Record<number, string>>({});
  const [lookupForm, setLookupForm] = useState({ nationalId: "", code: "" });
  const [message, setMessage] = useState("");

  const myTipsQuery = useQuery({
    queryKey: ["my-tips"],
    queryFn: listMyTips,
  });

  const queueQuery = useQuery({
    queryKey: ["tip-review-queue"],
    queryFn: listTipQueue,
    enabled: canReviewQueue,
  });

  const createTipMutation = useMutation({
    mutationFn: createTip,
    onSuccess: () => {
      setMessage("Tip submitted.");
      setTipForm({ case: "", person: "", content: "" });
      queryClient.invalidateQueries({ queryKey: ["my-tips"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const officerReviewMutation = useMutation({
    mutationFn: ({ tipId, approve, review }: { tipId: number; approve: boolean; review?: string }) =>
      officerReviewTip(tipId, approve, review),
    onSuccess: () => {
      setMessage("Officer review submitted.");
      queryClient.invalidateQueries({ queryKey: ["tip-review-queue"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const detectiveReviewMutation = useMutation({
    mutationFn: ({ tipId, approve, review }: { tipId: number; approve: boolean; review?: string }) =>
      detectiveReviewTip(tipId, approve, review),
    onSuccess: () => {
      setMessage("Detective review submitted.");
      queryClient.invalidateQueries({ queryKey: ["tip-review-queue"] });
    },
    onError: (error) => setMessage(extractApiError(error)),
  });

  const rewardLookupMutation = useMutation({
    mutationFn: ({ nationalId, code }: { nationalId: string; code: string }) => lookupReward(nationalId, code),
    onError: (error) => setMessage(extractApiError(error)),
  });

  const queueData = useMemo(() => queueQuery.data || [], [queueQuery.data]);

  return (
    <section className="page">
      <h1>Reward and Tips</h1>
      <p>Submit useful information, process officer/detective review queue, and lookup reward code payouts.</p>
      <ErrorAlert message={message} />

      <div className="cards-grid">
        <Card>
          <h2>Submit Tip</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createTipMutation.mutate({
                case: tipForm.case ? Number(tipForm.case) : undefined,
                person: tipForm.person ? Number(tipForm.person) : undefined,
                content: tipForm.content,
              });
            }}
          >
            <label>
              Case ID (optional)
              <input value={tipForm.case} onChange={(event) => setTipForm((prev) => ({ ...prev, case: event.target.value }))} />
            </label>
            <label>
              Suspect Person ID (optional)
              <input value={tipForm.person} onChange={(event) => setTipForm((prev) => ({ ...prev, person: event.target.value }))} />
            </label>
            <label>
              Tip Content
              <textarea value={tipForm.content} onChange={(event) => setTipForm((prev) => ({ ...prev, content: event.target.value }))} required />
            </label>
            <Button type="submit" disabled={createTipMutation.isPending}>
              Submit Tip
            </Button>
          </form>

          <div className="divider" />
          <h3>My Submitted Tips</h3>
          {myTipsQuery.isLoading && <Skeleton style={{ height: "3rem" }} />}
          {myTipsQuery.data?.length === 0 && <EmptyState title="No Tips" description="You have not submitted any tips yet." />}
          <div className="stack-list">
            {myTipsQuery.data?.map((tip) => (
              <div key={tip.id} className="queue-item">
                <strong>#{tip.id}</strong> {tip.content}
                <p className="muted-text">
                  {toTitleCase(tip.status)} | Created {formatDate(tip.created_at)}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {canReviewQueue && (
          <Card>
            <h2>Review Queue</h2>
            {queueQuery.isLoading && <Skeleton style={{ height: "3rem" }} />}
            {!queueQuery.isLoading && queueData.length === 0 && (
              <EmptyState title="Queue Empty" description="No tips are currently waiting for this role." />
            )}
            <div className="stack-list">
              {queueData.map((tip) => (
                <div key={tip.id} className="queue-item">
                  <div>
                    <strong>#{tip.id}</strong> {tip.content}
                    <p className="muted-text">Status: {toTitleCase(tip.status)}</p>
                  </div>
                  <textarea
                    placeholder="Review notes"
                    value={reviewMessage[tip.id] || ""}
                    onChange={(event) => setReviewMessage((prev) => ({ ...prev, [tip.id]: event.target.value }))}
                  />
                  <div className="button-row wrap">
                    {canReviewAsOfficer && (
                      <>
                        <Button onClick={() => officerReviewMutation.mutate({ tipId: tip.id, approve: true, review: reviewMessage[tip.id] })}>
                          Officer Approve
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => officerReviewMutation.mutate({ tipId: tip.id, approve: false, review: reviewMessage[tip.id] })}
                        >
                          Officer Reject
                        </Button>
                      </>
                    )}
                    {canReviewAsDetective && (
                      <>
                        <Button onClick={() => detectiveReviewMutation.mutate({ tipId: tip.id, approve: true, review: reviewMessage[tip.id] })}>
                          Detective Accept
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => detectiveReviewMutation.mutate({ tipId: tip.id, approve: false, review: reviewMessage[tip.id] })}
                        >
                          Detective Reject
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {canLookupReward && (
        <Card>
          <h2>Reward Lookup</h2>
          <div className="inline-form">
            <input
              placeholder="National ID"
              value={lookupForm.nationalId}
              onChange={(event) => setLookupForm((prev) => ({ ...prev, nationalId: event.target.value }))}
            />
            <input
              placeholder="Reward Code"
              value={lookupForm.code}
              onChange={(event) => setLookupForm((prev) => ({ ...prev, code: event.target.value }))}
            />
            <Button
              variant="secondary"
              onClick={() => rewardLookupMutation.mutate({ nationalId: lookupForm.nationalId, code: lookupForm.code })}
              disabled={!lookupForm.nationalId || !lookupForm.code || rewardLookupMutation.isPending}
            >
              Lookup
            </Button>
          </div>
          {rewardLookupMutation.data && (
            <div className="stack-list">
              <div className="queue-item">
                <p>
                  <strong>User:</strong> #{rewardLookupMutation.data.user.id} {rewardLookupMutation.data.user.username} (
                  {rewardLookupMutation.data.user.national_id})
                </p>
                <p>
                  <strong>Tip:</strong> {rewardLookupMutation.data.tip.content}
                </p>
                <p>
                  <strong>Reward Code:</strong> {rewardLookupMutation.data.reward.code}
                </p>
                <p>
                  <strong>Status:</strong> {toTitleCase(rewardLookupMutation.data.reward.status)} | <strong>Amount:</strong>{" "}
                  {formatMoney(rewardLookupMutation.data.reward.amount)}
                </p>
                <p>
                  <strong>Issued:</strong> {formatDate(rewardLookupMutation.data.reward.issued_at)} | <strong>Redeemed:</strong>{" "}
                  {formatDate(rewardLookupMutation.data.reward.redeemed_at)}
                </p>
              </div>
            </div>
          )}
        </Card>
      )}
    </section>
  );
}
