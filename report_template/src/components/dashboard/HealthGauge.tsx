import { StatusBadge } from "./StatusBadge";
import type { Report } from "@/data/mockReport";

interface HealthGaugeProps {
  score: number;
  status: Report["overall_status"];
}

export const HealthGauge = ({ score, status }: HealthGaugeProps) => {
  const radius = 80;
  const stroke = 10;
  const circumference = 2 * Math.PI * radius;
  const arc = circumference * 0.75;
  const offset = arc - (arc * score) / 100;

  const getColor = () => {
    if (score >= 85) return "hsl(var(--success))";
    if (score >= 60) return "hsl(var(--warning))";
    return "hsl(var(--error))";
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-48 h-40">
        <svg viewBox="0 0 200 170" className="w-full h-full">
          <circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke="hsl(var(--border))"
            strokeWidth={stroke}
            strokeDasharray={`${arc} ${circumference}`}
            strokeDashoffset={0}
            strokeLinecap="round"
            transform="rotate(135 100 100)"
          />
          <circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke={getColor()}
            strokeWidth={stroke}
            strokeDasharray={`${arc} ${circumference}`}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(135 100 100)"
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 6px ${getColor()}40)` }}
          />
          <text x="100" y="95" textAnchor="middle" className="fill-foreground text-4xl font-bold" fontSize="40">
            {score}
          </text>
          <text x="100" y="118" textAnchor="middle" className="fill-muted-foreground text-xs" fontSize="12">
            / 100
          </text>
        </svg>
      </div>
      <StatusBadge status={status} />
    </div>
  );
};
