import type { RoleSlug } from "../../api/types";

export type DashboardModule = {
  id: string;
  title: string;
  description: string;
  path: string;
  roles: RoleSlug[];
};

export const allModules: DashboardModule[] = [
  {
    id: "cases",
    title: "Case and Complaint Status",
    description: "Create, review, approve, reject, and update statuses according to workflow rules.",
    path: "/cases",
    roles: [
      "cadet",
      "police-officer",
      "patrol-officer",
      "detective",
      "sergeant",
      "captain",
      "police-chief",
      "system-administrator",
      "complainant",
      "base-user",
    ],
  },
  {
    id: "board",
    title: "Detective Board",
    description: "Drag-and-drop board with red-line links, evidence references, and report export.",
    path: "/board",
    roles: ["detective"],
  },
  {
    id: "evidence",
    title: "Evidence Registration & Review",
    description: "Register and update evidence types with access-level specific permissions.",
    path: "/evidence",
    roles: ["detective", "sergeant", "captain", "police-chief", "coroner", "police-officer", "patrol-officer", "system-administrator"],
  },
  {
    id: "reporting",
    title: "General Reporting",
    description: "View full case reports and submit trial verdict details when authorized.",
    path: "/reports",
    roles: ["judge", "captain", "police-chief", "system-administrator"],
  },
  {
    id: "wanted",
    title: "Most Wanted Intelligence",
    description: "Review ranking and rewards for long-running open suspect records.",
    path: "/most-wanted",
    roles: ["base-user", "cadet", "police-officer", "patrol-officer", "detective", "sergeant", "captain", "police-chief", "judge", "coroner", "system-administrator"],
  },
  {
    id: "rewards",
    title: "Tips and Rewards",
    description: "Submit tips, review queues, and lookup issued reward codes.",
    path: "/tips",
    roles: ["base-user", "police-officer", "detective", "system-administrator", "cadet", "patrol-officer", "sergeant", "captain", "police-chief", "coroner"],
  },
  {
    id: "payments",
    title: "Bail and Fine Payments",
    description: "Issue payment links for eligible case levels and monitor callback outcome.",
    path: "/payments",
    roles: ["sergeant", "system-administrator"],
  },
  {
    id: "admin",
    title: "Administration",
    description: "Manage roles and user access assignment without changing backend code.",
    path: "/admin",
    roles: ["system-administrator"],
  },
  {
    id: "notifications",
    title: "Notifications",
    description: "Track investigation and decision updates related to your assigned responsibilities.",
    path: "/notifications",
    roles: ["base-user", "detective", "sergeant", "captain", "police-chief", "system-administrator"],
  },
];
