import { describe, expect, it } from "vitest";
import { formatDate, formatMoney, toTitleCase } from "./format";

describe("format helpers", () => {
  it("formats money in rials", () => {
    expect(formatMoney(20000000)).toContain("20,000,000");
  });

  it("formats title strings from slug-like values", () => {
    expect(toTitleCase("pending_superior")).toBe("Pending Superior");
    expect(toTitleCase("police-chief")).toBe("Police Chief");
  });

  it("handles empty date", () => {
    expect(formatDate(null)).toBe("-");
  });
});
