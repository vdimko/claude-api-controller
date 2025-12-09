import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow-[0_0_8px_hsl(var(--primary)/_0.5)] hover:shadow-[0_0_12px_hsl(var(--primary))]",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow-[0_0_8px_hsl(var(--destructive)/_0.5)] hover:shadow-[0_0_12px_hsl(var(--destructive))]",
        outline: "text-foreground",
        success:
          "border-transparent bg-emerald-500 dark:bg-emerald-400 text-white dark:text-black shadow-[0_0_8px_hsl(160_100%_40%/_0.5)] hover:shadow-[0_0_12px_hsl(160_100%_40%)]",
        warning:
          "border-transparent bg-amber-500 dark:bg-yellow-400 text-white dark:text-black shadow-[0_0_8px_hsl(45_100%_50%/_0.5)] hover:shadow-[0_0_12px_hsl(45_100%_50%)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
