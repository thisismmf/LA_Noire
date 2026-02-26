import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { StatsOverview } from "../api/types";

async function fetchStats() {
  const { data } = await apiClient.get<StatsOverview>("/stats/overview/");
  return data;
}

export function HomePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["stats-overview"],
    queryFn: fetchStats,
  });

  return (
    <section className="page page-home">
      <div className="hero">
        <p className="kicker">Police Department Digital Transformation</p>
        <h1>LA Noire Investigation and Justice Platform</h1>
        <p>
          A role-aware operational portal for complaints, case progression, evidence analysis, suspect management, and trial
          reporting.
        </p>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <h2>Total Resolved Cases</h2>
          <strong>{isLoading ? "-" : data?.total_solved_cases ?? 0}</strong>
        </article>
        <article className="stat-card">
          <h2>Total Organization Employees</h2>
          <strong>{isLoading ? "-" : data?.total_employees ?? 0}</strong>
        </article>
        <article className="stat-card">
          <h2>Active Cases</h2>
          <strong>{isLoading ? "-" : data?.active_cases ?? 0}</strong>
        </article>
      </div>
    </section>
  );
}
