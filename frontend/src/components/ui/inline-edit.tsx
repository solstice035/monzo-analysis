import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface InlineEditProps {
  value: string;
  onSave: (newValue: string) => void;
  type?: "text" | "currency";
  placeholder?: string;
  className?: string;
  displayClassName?: string;
  isSaving?: boolean;
  disabled?: boolean;
}

export function InlineEdit({
  value,
  onSave,
  type = "text",
  placeholder = "Click to edit",
  className,
  displayClassName,
  isSaving = false,
  disabled = false,
}: InlineEditProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setEditValue(value);
  }, [value]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const displayValue =
    type === "currency"
      ? `£${(parseFloat(value) / 100).toFixed(2)}`
      : value || placeholder;

  const handleActivate = () => {
    if (disabled || isSaving) return;
    if (type === "currency") {
      // Show the raw number (pounds) for editing
      setEditValue((parseFloat(value) / 100).toFixed(2));
    } else {
      setEditValue(value);
    }
    setIsEditing(true);
  };

  const handleSave = () => {
    setIsEditing(false);
    let saveValue = editValue.trim();
    if (type === "currency") {
      // Strip £ sign, convert back to pence
      saveValue = saveValue.replace(/[£,]/g, "");
      const pence = Math.round(parseFloat(saveValue) * 100);
      if (!isNaN(pence) && pence.toString() !== value) {
        onSave(pence.toString());
      }
    } else {
      if (saveValue && saveValue !== value) {
        onSave(saveValue);
      }
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue(value);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleCancel();
    }
  };

  if (isSaving) {
    return (
      <span className={cn("inline-flex items-center gap-1.5", className)}>
        <Loader2 className="w-3 h-3 animate-spin text-stone" />
        <span className="text-stone">{displayValue}</span>
      </span>
    );
  }

  if (isEditing) {
    return (
      <input
        ref={inputRef}
        type={type === "currency" ? "number" : "text"}
        step={type === "currency" ? "0.01" : undefined}
        min={type === "currency" ? "0" : undefined}
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className={cn(
          "bg-navy-deep border border-coral/50 rounded px-2 py-0.5 text-white outline-none focus:border-coral transition-colors",
          type === "currency" && "text-right font-mono",
          className
        )}
        style={type === "currency" ? { fontFamily: "var(--font-mono)" } : undefined}
      />
    );
  }

  return (
    <span
      onClick={handleActivate}
      className={cn(
        "cursor-pointer rounded px-1 -mx-1 transition-colors hover:bg-navy-mid/50",
        disabled && "cursor-default hover:bg-transparent",
        displayClassName,
        className
      )}
      title={disabled ? undefined : "Click to edit"}
    >
      {displayValue}
    </span>
  );
}
