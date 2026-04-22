import { getRuntimeReport } from "@/data/runtimeReport";
import { HealthGauge } from "./HealthGauge";
import { StatCard } from "./StatCard";
import { StatusBadge } from "./StatusBadge";
import {
  CheckCircle, AlertTriangle, XCircle, Activity,
  TrendingUp, TrendingDown, FolderOpen, Layers, Database, Clock
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";

export const OverviewPage = () => {
  const r = getRuntimeReport();
  const checks = r.checks;
  const passed = checks.filter(c => c.status === "ok").length;
  const warnings = checks.filter(c => c.status === "warning").length;
  const errors = checks.filter(c => c.status === "error").length;
  const passRate = ((passed / checks.length) * 100).toFixed(1);
  const issueRate = (((warnings + errors) / checks.length) * 100).toFixed(1);

  const issueDistData = [
    { name: "OK", value: passed, fill: "hsl(var(--success))" },
    { name: "Warning", value: warnings, fill: "hsl(var(--warning))" },
    { name: "Error", value: errors, fill: "hsl(var(--error))" },
  ];

  const priorityFixes = checks
    .filter(c => c.status !== "ok")
    .sort((a, b) => (a.status === "error" ? -1 : 1))
    .map(c => ({
      name: c.name,
      status: c.status as "warning" | "error",
      summary: c.summary,
      suggestion: c.suggestions[0] || "Review manually",
    }));

  return (
    <div className="space-y-6">
    {/* Header */}
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{r.report_title}</h1>
          <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5" />{r.dataset_type}</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><Layers className="w-3.5 h-3.5" />{r.total_samples.toLocaleString()} samples</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{new Date(r.generation_timestamp).toLocaleString()}</span>
          </div>
        </div>
        <StatusBadge status={r.overall_status} />
      </div>
    </div>

    {/* Health + Stats */}
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-4 rounded-lg border border-border bg-card p-6 flex items-center justify-center">
        <HealthGauge score={r.health_score} status={r.overall_status} />
      </div>
      <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard label="Total Checks" value={checks.length} icon={Activity} variant="info" />
        <StatCard label="Passed" value={passed} icon={CheckCircle} variant="success" />
        <StatCard label="Warnings" value={warnings} icon={AlertTriangle} variant="warning" />
        <StatCard label="Errors" value={errors} icon={XCircle} variant="error" />
        <StatCard label="Pass Rate" value={`${passRate}%`} icon={TrendingUp} variant="success" />
        <StatCard label="Issue Rate" value={`${issueRate}%`} icon={TrendingDown} variant="error" />
      </div>
    </div>

    {/* What to Fix + Issue Distribution */}
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div className="lg:col-span-7 rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-warning" /> What to Fix First
        </h3>
        <div className="space-y-3">
          {priorityFixes.map((fix) => (
            <div key={fix.name} className="rounded-md border border-border bg-surface-0 p-3">
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status={fix.status} />
                <span className="text-sm font-medium capitalize">{fix.name.replace(/_/g, " ")}</span>
              </div>
              <p className="text-xs text-muted-foreground mb-1.5">{fix.summary}</p>
              <p className="text-xs text-info">→ {fix.suggestion}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="lg:col-span-5 rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold mb-4">Issue Distribution</h3>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={issueDistData} barSize={40}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "hsl(var(--surface-2))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {issueDistData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>

    {/* Dataset Info */}
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="text-sm font-semibold mb-3">Dataset Info</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Path</p>
          <p className="font-mono text-xs mt-0.5 truncate" title={r.dataset_path}>{r.dataset_path}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Splits</p>
          <div className="flex gap-1 mt-1 flex-wrap">
            {r.splits_available.map(s => (
              <span key={s} className="px-2 py-0.5 rounded text-xs bg-surface-2 text-muted-foreground">{s}</span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Classes</p>
          <p className="font-semibold mt-0.5">{r.num_classes}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Splits Count</p>
          <p className="font-semibold mt-0.5">{r.splits_available.length}</p>
        </div>
      </div>
    </div>
    </div>
  );
};
