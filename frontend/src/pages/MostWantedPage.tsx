import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";
import { formatMoney } from "../utils/format";

type MostWantedEntry = {
  person: {
    id: number;
    full_name: string;
    national_id: string;
    phone: string;
    photo: string | null;
    notes: string;
  };
  days_wanted: number;
  crime_degree: number;
  ranking_score: number;
  reward_amount: number;
};

async function fetchMostWanted() {
  const { data } = await apiClient.get<MostWantedEntry[]>("/public/most-wanted/");
  return data;
}

export function MostWantedPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["most-wanted-public"],
    queryFn: fetchMostWanted,
  });

  return (
    <section className="page">
      <h1>Most Wanted</h1>
      <p>Ranking and reward formula are based on wanted duration and maximum crime level.</p>
      <ErrorAlert message={extractApiError(error, "")} />
      <div className="cards-grid">
        {isLoading &&
          Array.from({ length: 3 }).map((_, idx) => (
            <Card key={`skeleton-${idx}`}>
              <Skeleton style={{ height: "1.2rem", width: "70%", marginBottom: "0.5rem" }} />
              <Skeleton />
              <Skeleton />
              <Skeleton />
            </Card>
          ))}
        {data?.length === 0 && !isLoading && (
          <EmptyState
            title="No Most Wanted Entries"
            description="No suspect has been wanted for more than one month in an open case yet."
          />
        )}
        {data?.map((entry) => (
          <Card key={entry.person.id} className="info-card">
            <h2>{entry.person.full_name}</h2>
            <p>Days Wanted: {entry.days_wanted}</p>
            <p>Crime Degree: {entry.crime_degree}</p>
            <p>Ranking Score: {entry.ranking_score}</p>
            <p>Reward: {formatMoney(entry.reward_amount)}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
