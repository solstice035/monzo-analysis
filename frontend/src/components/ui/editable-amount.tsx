import { useState, useRef, useEffect } from "react";
import { cn, formatCurrency } from "@/lib/utils";

export interface EditableAmountProps {
  /** Current value in pence */
  value: number;
  /** Called with new value in pence on save */
  onSave: (newValue: number) => Promise<void>;
  /** Additional className for the container */
  className?: string;
  /** Tabindex for keyboard navigation */
  tabIndex?: number;
}

export function EditableAmount({
  value,
  onSave,
  className,
  tabIndex,
}: EditableAmountProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const displayValue = formatCurrency(value);

  const startEditing = () => {
    setEditValue((value / 100).toFixed(2));
    setIsEditing(true);
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = async () => {
    const newPence = Math.round(parseFloat(editValue) * 100);
    if (isNaN(newPence) || newPence <= 0) {
      setIsEditing(false);
      return;
    }
    if (newPence === value) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    try {
      await onSave(newPence);
    } catch {
      // Rollback: value hasn't changed in parent state
    } finally {
      setIsSaving(false);
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSave();
    }
    if (e.key === "Escape") {
      setIsEditing(false);
    }
    if (e.key === "Tab") {
      handleSave();
    }
  };

  if (isEditing) {
    return (
      <input
        ref={inputRef}
        type="number"
        step="0.01"
        min="0"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className={cn(
          "bg-navy border-2 border-coral rounded px-1.5 py-0.5",
          "text-sm font-mono text-white text-right w-24",
          "focus:outline-none",
          className
        )}
        style={{ fontFamily: "var(--font-mono)" }}
      />
    );
  }

  return (
    <button
      onClick={startEditing}
      tabIndex={tabIndex}
      className={cn(
        "text-sm text-right text-white px-1.5 py-0.5 rounded tabular-nums",
        "hover:bg-navy-mid/50 cursor-text transition-colors",
        isSaving && "opacity-50",
        className
      )}
      style={{ fontFamily: "var(--font-mono)" }}
    >
      {isSaving ? "..." : displayValue}
    </button>
  );
}
