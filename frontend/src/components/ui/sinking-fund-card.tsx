import { forwardRef, type HTMLAttributes } from "react";
import { cn, formatCurrency } from "@/lib/utils";
import type { SinkingFundStatus } from "@/lib/api";

export interface SinkingFundCardProps extends HTMLAttributes<HTMLDivElement> {
  fund: SinkingFundStatus;
}

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const SinkingFundCard = forwardRef<HTMLDivElement, SinkingFundCardProps>(
  ({ className, fund, ...props }, ref) => {
    const percentage = fund.target_amount > 0
      ? Math.min(((fund.pot_balance || 0) / fund.target_amount) * 100, 100)
      : 0;

    const isOnTrack = fund.on_track;
    const hasVariance = fund.variance !== 0;

    let statusColor = "border-mint";
    let statusBg = "bg-mint/10";
    let statusText = "text-mint";
    if (!isOnTrack) {
      statusColor = "border-coral";
      statusBg = "bg-coral/10";
      statusText = "text-coral";
    } else if (hasVariance && fund.variance < 0) {
      statusColor = "border-yellow";
      statusBg = "bg-yellow/10";
      statusText = "text-yellow";
    }

    const targetMonthName = fund.target_month
      ? MONTH_NAMES[fund.target_month - 1]
      : "Year end";

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-2xl p-4 bg-gradient-to-br from-charcoal to-navy-deep border transition-all duration-200",
          statusColor,
          className
        )}
        {...props}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎯</span>
            <div>
              <h3 className="font-semibold text-white">
                {fund.budget_name || fund.category}
              </h3>
              {fund.pot_name && (
                <span className="text-xs text-sky">
                  Linked to {fund.pot_name}
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <div
              className="font-display text-2xl text-white"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {formatCurrency(fund.pot_balance || 0)}
            </div>
            <div className="text-xs text-stone">
              of {formatCurrency(fund.target_amount)}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="h-3 bg-navy rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                isOnTrack
                  ? "bg-gradient-to-r from-sky to-[#7DD3FC]"
                  : "bg-gradient-to-r from-coral-deep to-coral"
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="bg-navy/50 rounded-lg p-2 text-center">
            <div className="text-xs text-stone mb-1">Monthly</div>
            <div
              className="text-sm text-white font-medium"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(fund.monthly_contribution)}
            </div>
          </div>
          <div className="bg-navy/50 rounded-lg p-2 text-center">
            <div className="text-xs text-stone mb-1">Months left</div>
            <div
              className="text-sm text-white font-medium"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {fund.months_remaining}
            </div>
          </div>
          <div className="bg-navy/50 rounded-lg p-2 text-center">
            <div className="text-xs text-stone mb-1">Due</div>
            <div className="text-sm text-white font-medium">
              {targetMonthName}
            </div>
          </div>
        </div>

        {/* Status and projection */}
        <div className="flex items-center justify-between">
          <span
            className={cn(
              "px-2 py-1 rounded-full text-xs font-medium",
              statusBg,
              statusText
            )}
          >
            {isOnTrack ? "On track" : "Behind"}
          </span>
          <span className="text-xs text-stone">
            {fund.variance > 0 ? (
              <span className="text-mint">
                +{formatCurrency(fund.variance)} ahead
              </span>
            ) : fund.variance < 0 ? (
              <span className="text-coral">
                {formatCurrency(Math.abs(fund.variance))} behind
              </span>
            ) : (
              "Right on target"
            )}
          </span>
        </div>

        {/* Projection */}
        <div className="mt-3 pt-3 border-t border-navy-mid">
          <div className="flex items-center justify-between text-xs">
            <span className="text-stone">Projected at target date:</span>
            <span
              className={cn(
                "font-medium",
                fund.projected_balance >= fund.target_amount
                  ? "text-mint"
                  : "text-coral"
              )}
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {formatCurrency(fund.projected_balance)}
            </span>
          </div>
        </div>
      </div>
    );
  }
);
SinkingFundCard.displayName = "SinkingFundCard";

export { SinkingFundCard };
