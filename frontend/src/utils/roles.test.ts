import { describe, expect, it } from "vitest";
import { hasAnyRole, isEmployee } from "./roles";

describe("roles utilities", () => {
  it("detects intersection in role arrays", () => {
    const result = hasAnyRole(["base-user", "detective"], ["captain", "detective"]);
    expect(result).toBe(true);
  });

  it("returns false when no role matches", () => {
    const result = hasAnyRole(["base-user"], ["captain", "sergeant"]);
    expect(result).toBe(false);
  });

  it("identifies employee role set", () => {
    expect(isEmployee(["base-user"])).toBe(false);
    expect(isEmployee(["cadet"])).toBe(true);
  });
});
