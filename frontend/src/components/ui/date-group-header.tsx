import { formatCurrency } from "@/lib/utils";

export interface DateGroupHeaderProps {
  label: string;
  dayTotal: number;
}

export function DateGroupHeader({ label, dayTotal }: DateGroupHeaderProps) {
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-navy-deep/30 border-b border-navy-mid sticky top-[52px] z-[5]">
      <span className="text-[0.7rem] font-semibold text-stone uppercase tracking-wider">
        {label}
      </span>
      <span
        className="text-[0.7rem] text-stone tabular-nums"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        {dayTotal < 0 ? "-" : "+"}
        {formatCurrency(Math.abs(dayTotal))}
      </span>
    </div>
  );
}
