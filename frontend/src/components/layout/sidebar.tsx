import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Receipt,
  PiggyBank,
  Settings,
  Workflow,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transactions", label: "Transactions", icon: Receipt },
  { to: "/budgets", label: "Budgets", icon: PiggyBank },
  { to: "/rules", label: "Rules", icon: Workflow },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="w-64 h-screen bg-charcoal border-r border-navy-mid flex flex-col fixed left-0 top-0">
      {/* Logo */}
      <div className="p-6 border-b border-navy-mid">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-coral rounded-lg flex items-center justify-center shadow-[0_0_30px_rgba(255,90,95,0.4)]">
            <span
              className="text-white text-xl"
              style={{ fontFamily: "var(--font-display)" }}
            >
              M
            </span>
          </div>
          <span
            className="text-white text-lg tracking-wider"
            style={{ fontFamily: "var(--font-display)" }}
          >
            MONZO ANALYSIS
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6">
        <ul className="space-y-1 px-3">
          {navItems.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all",
                    isActive
                      ? "bg-coral/10 text-coral"
                      : "text-stone hover:text-white hover:bg-navy-mid"
                  )
                }
              >
                <Icon className="w-5 h-5" />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-6 border-t border-navy-mid">
        <div className="text-xs text-slate">
          Last sync: <span className="text-stone">2 hours ago</span>
        </div>
      </div>
    </aside>
  );
}
