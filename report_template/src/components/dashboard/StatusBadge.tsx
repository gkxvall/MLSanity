import { cn } from "@/lib/utils";

const statusConfig = {
  ok: { label: "OK", className: "bg-success/15 text-success border-success/30" },
  healthy: { label: "Healthy", className: "bg-success/15 text-success border-success/30" },
  warning: { label: "Warning", className: "bg-warning/15 text-warning border-warning/30" },
  acceptable: { label: "Acceptable", className: "bg-warning/15 text-warning border-warning/30" },
  needs_attention: { label: "Needs Attention", className: "bg-warning/15 text-warning border-warning/30" },
  error: { label: "Error", className: "bg-error/15 text-error border-error/30" },
  critical: { label: "Critical", className: "bg-error/15 text-error border-error/30" },
};

interface StatusBadgeProps {
  status: keyof typeof statusConfig;
  label?: string;
  className?: string;
}

export const StatusBadge = ({ status, label, className }: StatusBadgeProps) => {
  const config = statusConfig[status];
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
      config.className,
      className
    )}>
      <span className={cn(
        "w-1.5 h-1.5 rounded-full mr-1.5",
        status === "ok" || status === "healthy" ? "bg-success" :
        status === "warning" || status === "acceptable" || status === "needs_attention" ? "bg-warning" :
        "bg-error"
      )} />
      {label || config.label}
    </span>
  );
};
