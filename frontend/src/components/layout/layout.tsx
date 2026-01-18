import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";

export function Layout() {
  return (
    <div className="min-h-screen bg-navy">
      <Sidebar />
      <main className="ml-64 p-8">
        <Outlet />
      </main>
    </div>
  );
}
