import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";

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
  const { data, isLoading } = useQuery({
    queryKey: ["most-wanted-public"],
    queryFn: fetchMostWanted,
  });

  return (
    <section className="page">
      <h1>Most Wanted</h1>
      <p>Ranking and reward formula are based on wanted duration and maximum crime level.</p>
      <div className="cards-grid">
        {isLoading && <p>Loading...</p>}
        {data?.length === 0 && !isLoading && <p>No suspect has reached the Most Wanted threshold yet.</p>}
        {data?.map((entry) => (
          <article key={entry.person.id} className="info-card">
            <h2>{entry.person.full_name}</h2>
            <p>Days Wanted: {entry.days_wanted}</p>
            <p>Crime Degree: {entry.crime_degree}</p>
            <p>Ranking Score: {entry.ranking_score}</p>
            <p>Reward: {entry.reward_amount.toLocaleString()} Rials</p>
          </article>
        ))}
      </div>
    </section>
  );
}
