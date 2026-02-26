import { describe, expect, it } from "vitest";
import { allModules } from "./modules";
import { hasAnyRole } from "../../utils/roles";

describe("dashboard module matrix", () => {
  it("includes detective board for detective role", () => {
    const modules = allModules.filter((module) => hasAnyRole(["detective"], module.roles));
    expect(modules.some((module) => module.id === "board")).toBe(true);
  });

  it("limits admin panel to system administrator role", () => {
    const detectiveModules = allModules.filter((module) => hasAnyRole(["detective"], module.roles));
    const adminModules = allModules.filter((module) => hasAnyRole(["system-administrator"], module.roles));
    expect(detectiveModules.some((module) => module.id === "admin")).toBe(false);
    expect(adminModules.some((module) => module.id === "admin")).toBe(true);
  });
});
