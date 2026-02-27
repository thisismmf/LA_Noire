import { createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "../components/layout/PublicLayout";
import { AppLayout } from "../components/layout/AppLayout";
import { RequireAuth } from "../features/auth/RequireAuth";
import { RoleGuard } from "../features/auth/RoleGuard";
import { HomePage } from "../pages/HomePage";
import { MostWantedPage } from "../pages/MostWantedPage";
import { AuthPage } from "../pages/AuthPage";
import { DashboardPage } from "../pages/DashboardPage";
import { CasesPage } from "../pages/CasesPage";
import { DetectiveBoardPage } from "../pages/DetectiveBoardPage";
import { EvidencePage } from "../pages/EvidencePage";
import { ReportsPage } from "../pages/ReportsPage";
import { AdminPanelPage } from "../pages/AdminPanelPage";
import { TipsRewardsPage } from "../pages/TipsRewardsPage";
import { PaymentsPage } from "../pages/PaymentsPage";
import { NotificationsPage } from "../pages/NotificationsPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <PublicLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "auth",
        element: <AuthPage />,
      },
      {
        path: "most-wanted",
        element: <MostWantedPage />,
      },
      {
        element: <RequireAuth />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { path: "dashboard", element: <DashboardPage /> },
              { path: "cases", element: <CasesPage /> },
              {
                element: <RoleGuard allowedRoles={["detective"]} />,
                children: [{ path: "board", element: <DetectiveBoardPage /> }],
              },
              { path: "evidence", element: <EvidencePage /> },
              { path: "reports", element: <ReportsPage /> },
              { path: "tips", element: <TipsRewardsPage /> },
              { path: "notifications", element: <NotificationsPage /> },
              {
                element: <RoleGuard allowedRoles={["sergeant", "system-administrator"]} />,
                children: [{ path: "payments", element: <PaymentsPage /> }],
              },
              {
                element: <RoleGuard allowedRoles={["system-administrator"]} />,
                children: [{ path: "admin", element: <AdminPanelPage /> }],
              },
            ],
          },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
