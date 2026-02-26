import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../api/client";
import type { StatsOverview } from "../api/types";
import { Card } from "../components/ui/Card";
import { ErrorAlert } from "../components/ui/ErrorAlert";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiError } from "../utils/errors";

async function fetchStats() {
  const { data } = await apiClient.get<StatsOverview>("/stats/overview/");
  return data;
}

export function HomePage() {
  const { data, isLoading, error } = useQuery({
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
        <div className="hero-actions">
          <Link to="/auth" className="primary-button inline-block">
            Enter Secure Portal
          </Link>
          <Link to="/most-wanted" className="secondary-link">
            View Public Most Wanted
          </Link>
        </div>
      </div>

      <ErrorAlert message={extractApiError(error, "")} />
      <div className="stats-grid">
        <Card className="stat-card">
          <h2>Total Resolved Cases</h2>
          <strong>{isLoading ? <Skeleton style={{ height: "2rem" }} /> : data?.total_solved_cases ?? 0}</strong>
        </Card>
        <Card className="stat-card">
          <h2>Total Organization Employees</h2>
          <strong>{isLoading ? <Skeleton style={{ height: "2rem" }} /> : data?.total_employees ?? 0}</strong>
        </Card>
        <Card className="stat-card">
          <h2>Active Cases</h2>
          <strong>{isLoading ? <Skeleton style={{ height: "2rem" }} /> : data?.active_cases ?? 0}</strong>
        </Card>
      </div>
    </section>
  );
}
