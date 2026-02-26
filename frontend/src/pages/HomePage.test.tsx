import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HomePage } from "./HomePage";
import { renderWithProviders } from "../test/testUtils";

vi.mock("../api/client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({
      data: {
        total_solved_cases: 10,
        total_employees: 25,
        active_cases: 4,
      },
    }),
  },
}));

describe("HomePage", () => {
  it("renders overview stats from API", async () => {
    renderWithProviders(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
    });
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });
});
