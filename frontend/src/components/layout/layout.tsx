import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { ErrorBoundary } from "@/components/error-boundary";

export function Layout() {
  return (
    <div className="min-h-screen bg-navy">
      <Sidebar />
      <main className="ml-64 p-8">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
}
