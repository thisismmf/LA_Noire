import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { formatDate, toTitleCase } from "../utils/format";
import { listNotifications, markNotificationRead } from "./notificationsApi";

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["notifications"],
    queryFn: listNotifications,
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <section className="page">
      <h1>Notifications</h1>
      <p>Detective and workflow notifications including evidence updates, decisions, and reward code issuance.</p>
      <ErrorAlert message={extractApiError(error, "")} />

      <Card>
        <h2>Inbox</h2>
        {isLoading && <Skeleton style={{ height: "3rem" }} />}
        {!isLoading && data?.length === 0 && (
          <EmptyState title="No Notifications" description="You do not have pending notifications right now." />
        )}
        <div className="stack-list">
          {data?.map((item) => (
            <div key={item.id} className={`queue-item ${item.read_at ? "" : "unread-row"}`}>
              <div>
                <strong>#{item.id}</strong> {toTitleCase(item.type)}
                <p className="muted-text">
                  Case: {item.case || "-"} | Created: {formatDate(item.created_at)} | Read: {formatDate(item.read_at)}
                </p>
                <p>{JSON.stringify(item.payload)}</p>
              </div>
              {!item.read_at && (
                <Button
                  variant="secondary"
                  onClick={() => markReadMutation.mutate(item.id)}
                  disabled={markReadMutation.isPending}
                >
                  Mark as Read
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
