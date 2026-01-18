import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-bold text-sm uppercase tracking-wide transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-coral focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-coral text-white shadow-[0_4px_20px_rgba(255,90,95,0.4)] hover:translate-y-[-3px] hover:shadow-[0_8px_40px_rgba(255,90,95,0.6)]",
        secondary:
          "bg-transparent text-white border-2 border-white hover:bg-white hover:text-navy",
        mint: "bg-mint text-navy hover:translate-y-[-3px] hover:shadow-[0_8px_40px_rgba(0,217,181,0.5)]",
        ghost: "text-stone hover:text-white hover:bg-navy-mid",
        link: "text-coral underline-offset-4 hover:underline",
      },
      size: {
        default: "px-6 py-3",
        sm: "px-4 py-2 text-xs",
        lg: "px-8 py-4 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
