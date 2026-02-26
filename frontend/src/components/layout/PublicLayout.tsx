import { Outlet } from "react-router-dom";
import { TopNav } from "./TopNav";

export function PublicLayout() {
  return (
    <div className="root-layout">
      <TopNav />
      <Outlet />
    </div>
  );
}
