import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { AccountSelector } from "@/components/account-selector";
import { useAnnualView } from "@/hooks/useApi";
import { formatCurrency } from "@/lib/utils";
import { Download } from "lucide-react";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function statusBg(status: "under" | "on_track" | "over"): string {
  switch (status) {
    case "under":
      return "bg-mint/10";
    case "on_track":
      return "bg-yellow/10";
    case "over":
      return "bg-coral/10";
  }
}

function statusText(status: "under" | "on_track" | "over"): string {
  switch (status) {
    case "under":
      return "text-mint";
    case "on_track":
      return "text-yellow";
    case "over":
      return "text-coral";
  }
}

export function Annual() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const { data, isLoading } = useAnnualView(year);

  const yearOptions = [currentYear - 1, currentYear, currentYear + 1];

  // CSV export
  const exportCsv = useCallback(() => {
    if (!data) return;

    const headers = ["Group", ...MONTHS, "Total Spent", "Total Allocated"];
    const rows = data.groups.map((group) => {
      const monthCells = MONTHS.map((_, i) => {
        const m = group.months.find((mo) => mo.month === i + 1);
        return m ? (m.spent / 100).toFixed(2) : "0.00";
      });
      return [
        group.group_name,
        ...monthCells,
        (group.total_spent / 100).toFixed(2),
        (group.total_allocated / 100).toFixed(2),
      ];
    });

    // Totals row
    const totalCells = MONTHS.map((_, i) => {
      const t = data.monthly_totals.find((mt) => mt.month === i + 1);
      return t ? (t.spent / 100).toFixed(2) : "0.00";
    });
    rows.push([
      "TOTAL",
      ...totalCells,
      (data.grand_total.spent / 100).toFixed(2),
      (data.grand_total.allocated / 100).toFixed(2),
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `annual-budget-${year}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, year]);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1
          className="text-3xl text-white"
          style={{ fontFamily: "var(--font-display)" }}
        >
          ANNUAL VIEW
        </h1>
        <div className="flex items-center gap-4">
          <AccountSelector />
          <button
            onClick={exportCsv}
            disabled={!data}
            className="flex items-center gap-2 px-5 py-2 bg-coral text-white rounded-full text-sm font-medium hover:bg-coral-bright transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Year Selector */}
      <div className="flex gap-1 mb-6">
        {yearOptions.map((y) => (
          <button
            key={y}
            onClick={() => setYear(y)}
            className={`px-5 py-1.5 rounded-full text-sm font-medium transition-all ${
              year === y
                ? "bg-coral text-white"
                : "bg-navy-deep text-stone hover:bg-navy-mid hover:text-white"
            }`}
          >
            {y}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-stone">
          Loading annual data...
        </div>
      ) : !data || data.groups.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-stone">
              No annual data available for {year}. Create budgets and sync
              transactions.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-navy-mid">
                    <th className="text-left text-stone font-medium p-3 sticky left-0 bg-charcoal z-10 min-w-[140px]">
                      Group
                    </th>
                    {MONTHS.map((m) => (
                      <th
                        key={m}
                        className="text-center text-stone font-medium p-3 min-w-[90px]"
                      >
                        {m}
                      </th>
                    ))}
                    <th className="text-center text-stone font-medium p-3 min-w-[100px]">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.groups.map((group) => (
                    <tr
                      key={group.group_id}
                      className="border-b border-navy-mid/50 hover:bg-navy/30"
                    >
                      <td className="p-3 text-white font-medium sticky left-0 bg-charcoal z-10">
                        {group.group_name}
                      </td>
                      {MONTHS.map((_, i) => {
                        const m = group.months.find(
                          (mo) => mo.month === i + 1
                        );
                        if (!m || !m.period_id) {
                          return (
                            <td
                              key={i}
                              className="p-3 text-center text-stone/40"
                            >
                              —
                            </td>
                          );
                        }
                        return (
                          <td
                            key={i}
                            className={`p-3 text-center rounded ${statusBg(m.status)}`}
                          >
                            <div className={`font-medium ${statusText(m.status)}`}>
                              {formatCurrency(m.spent)}
                            </div>
                            <div className="text-xs text-stone/60">
                              / {formatCurrency(m.allocated)}
                            </div>
                          </td>
                        );
                      })}
                      <td className="p-3 text-center">
                        <div className="text-white font-medium">
                          {formatCurrency(group.total_spent)}
                        </div>
                        <div className="text-xs text-stone/60">
                          / {formatCurrency(group.total_allocated)}
                        </div>
                      </td>
                    </tr>
                  ))}

                  {/* Totals Row */}
                  <tr className="border-t-2 border-navy-mid bg-navy/20">
                    <td
                      className="p-3 font-bold text-white sticky left-0 bg-charcoal z-10"
                      style={{ fontFamily: "var(--font-display)" }}
                    >
                      TOTAL
                    </td>
                    {MONTHS.map((_, i) => {
                      const t = data.monthly_totals.find(
                        (mt) => mt.month === i + 1
                      );
                      if (!t) {
                        return (
                          <td
                            key={i}
                            className="p-3 text-center text-stone/40"
                          >
                            —
                          </td>
                        );
                      }
                      return (
                        <td key={i} className="p-3 text-center">
                          <div className="text-white font-medium">
                            {formatCurrency(t.spent)}
                          </div>
                          <div className="text-xs text-stone/60">
                            / {formatCurrency(t.allocated)}
                          </div>
                        </td>
                      );
                    })}
                    <td className="p-3 text-center">
                      <div
                        className="text-white font-bold"
                        style={{ fontFamily: "var(--font-display)" }}
                      >
                        {formatCurrency(data.grand_total.spent)}
                      </div>
                      <div className="text-xs text-stone/60">
                        / {formatCurrency(data.grand_total.allocated)}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
