import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  variant?: "default" | "success" | "warning" | "error" | "info";
}

const variantClasses = {
  default: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  error: "text-error",
  info: "text-info",
};

export const StatCard = ({ label, value, icon: Icon, variant = "default" }: StatCardProps) => (
  <div className="rounded-lg border border-border bg-card p-4 flex items-start gap-3">
    <div className={cn("p-2 rounded-md bg-surface-2", variantClasses[variant])}>
      <Icon className="w-4 h-4" />
    </div>
    <div className="min-w-0">
      <p className="text-xs text-muted-foreground truncate">{label}</p>
      <p className={cn("text-xl font-semibold mt-0.5", variantClasses[variant])}>{value}</p>
    </div>
  </div>
);
