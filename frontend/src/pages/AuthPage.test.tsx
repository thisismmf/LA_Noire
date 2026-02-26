import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthPage } from "./AuthPage";
import { renderWithProviders } from "../test/testUtils";

vi.mock("../features/auth/authApi", () => ({
  login: vi.fn(),
  register: vi.fn(),
  fetchMe: vi.fn(),
}));

describe("AuthPage", () => {
  beforeEach(() => {
    renderWithProviders(<AuthPage />);
  });

  it("shows login form by default and can switch to register", async () => {
    expect(screen.getByText("Sign In")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(screen.getByRole("button", { name: "Create Account" })).toBeInTheDocument();
  });
});
