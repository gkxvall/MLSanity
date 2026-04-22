import { useState } from "react";
import { getRuntimeReport } from "@/data/runtimeReport";
import type { Check } from "@/data/mockReport";
import { StatCard } from "./StatCard";
import { StatusBadge } from "./StatusBadge";
import { CodeBlock } from "./CodeBlock";
import { Activity, CheckCircle, AlertTriangle, XCircle, ArrowRight } from "lucide-react";

const LabelHintsTable = ({ candidates }: { candidates: any[] }) => (
  <div className="overflow-x-auto scrollbar-thin">
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border text-left text-muted-foreground">
          <th className="pb-2 pr-4 font-medium">Sample ID</th>
          <th className="pb-2 pr-4 font-medium">Current</th>
          <th className="pb-2 pr-4 font-medium">Suspected</th>
          <th className="pb-2 pr-4 font-medium">Score</th>
          <th className="pb-2 font-medium">Reason</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c: any, i: number) => (
          <tr key={i} className="border-b border-border/50 hover:bg-surface-2/50 transition-colors">
            <td className="py-2 pr-4 font-mono text-info">{c.sample_id}</td>
            <td className="py-2 pr-4"><span className="px-1.5 py-0.5 rounded bg-error/10 text-error text-xs">{c.current_label}</span></td>
            <td className="py-2 pr-4"><span className="px-1.5 py-0.5 rounded bg-success/10 text-success text-xs">{c.suspected_label}</span></td>
            <td className="py-2 pr-4 font-mono">{c.score.toFixed(2)}</td>
            <td className="py-2 text-muted-foreground">{c.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const PairTable = ({ pairs, labelA, labelB, distanceKey }: { pairs: any[]; labelA: string; labelB: string; distanceKey?: string }) => (
  <div className="overflow-x-auto scrollbar-thin">
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border text-left text-muted-foreground">
          <th className="pb-2 pr-4 font-medium">{labelA}</th>
          <th className="pb-2 pr-4 font-medium">{labelB}</th>
          {distanceKey && <th className="pb-2 font-medium">{distanceKey === "similarity" ? "Similarity" : "Distance"}</th>}
        </tr>
      </thead>
      <tbody>
        {pairs.map((p: any, i: number) => (
          <tr key={i} className="border-b border-border/50 hover:bg-surface-2/50 transition-colors">
            <td className="py-2 pr-4 font-mono text-info">{p[Object.keys(p)[0]]}</td>
            <td className="py-2 pr-4 font-mono text-info">{p[Object.keys(p)[1]]}</td>
            {distanceKey && <td className="py-2 font-mono">{p[distanceKey]?.toFixed(3)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const GroupTable = ({ groups }: { groups: any[] }) => (
  <div className="overflow-x-auto scrollbar-thin">
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border text-left text-muted-foreground">
          <th className="pb-2 pr-4 font-medium">Group</th>
          <th className="pb-2 pr-4 font-medium">Samples</th>
          <th className="pb-2 font-medium">Hash</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g: any, i: number) => (
          <tr key={i} className="border-b border-border/50 hover:bg-surface-2/50 transition-colors">
            <td className="py-2 pr-4 font-mono">#{g.group_id}</td>
            <td className="py-2 pr-4">
              <div className="flex gap-1 flex-wrap">
                {g.sample_ids.map((id: string) => (
                  <span key={id} className="px-1.5 py-0.5 rounded bg-surface-2 text-info font-mono text-xs">{id}</span>
                ))}
              </div>
            </td>
            <td className="py-2 font-mono text-muted-foreground">{g.hash}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const CheckDetail = ({ check }: { check: Check }) => {
  const d = check.details;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center gap-3 mb-2">
          <h3 className="text-base font-semibold capitalize">{check.name.replace(/_/g, " ")}</h3>
          <StatusBadge status={check.status} />
        </div>
        <p className="text-sm text-muted-foreground">{check.summary}</p>
        {check.suggestions.length > 0 && (
          <div className="mt-3 space-y-1.5">
            <p className="text-xs font-medium text-muted-foreground">Suggestions</p>
            {check.suggestions.map((s, i) => (
              <p key={i} className="text-xs text-info flex items-start gap-1.5">
                <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> {s}
              </p>
            ))}
          </div>
        )}
      </div>

      {/* Metrics */}
      {d && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Metrics</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            {Object.entries(d).filter(([, v]) => typeof v === "number" || typeof v === "string").map(([k, v]) => (
              <div key={k}>
                <p className="text-xs text-muted-foreground">{k.replace(/_/g, " ")}</p>
                <p className="font-mono font-medium mt-0.5">{typeof v === "number" ? (v < 1 && v > 0 ? v.toFixed(4) : v.toLocaleString()) : String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rich tables */}
      {check.name === "label_hints" && d.candidates && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Suspicious Samples</h4>
          <LabelHintsTable candidates={d.candidates} />
        </div>
      )}

      {check.name === "duplicates" && d.groups && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Duplicate Groups</h4>
          <GroupTable groups={d.groups} />
        </div>
      )}

      {check.name === "near_duplicates" && d.pair_examples && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Near-Duplicate Pairs</h4>
          <PairTable pairs={d.pair_examples} labelA="Sample A" labelB="Sample B" distanceKey="similarity" />
        </div>
      )}

      {check.name === "leakage" && d.leaked_pairs && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Leaked Pairs</h4>
          <PairTable pairs={d.leaked_pairs} labelA="Train ID" labelB="Test ID" />
          {d.affected_classes && (
            <div className="mt-3">
              <p className="text-xs text-muted-foreground mb-1">Affected Classes</p>
              <div className="flex gap-1 flex-wrap">
                {d.affected_classes.map((c: string) => (
                  <span key={c} className="px-2 py-0.5 rounded bg-error/10 text-error text-xs">{c}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {check.name === "leakage_near" && d.pair_examples && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Near-Leakage Pairs</h4>
          <PairTable pairs={d.pair_examples} labelA="Train ID" labelB="Test ID" distanceKey="distance" />
        </div>
      )}

      {check.name === "imbalance" && d.largest_class && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Imbalance Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">Largest Class</p>
              <p className="font-medium mt-0.5">{d.largest_class.name} <span className="text-muted-foreground">({d.largest_class.count.toLocaleString()})</span></p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Smallest Class</p>
              <p className="font-medium mt-0.5">{d.smallest_class.name} <span className="text-muted-foreground">({d.smallest_class.count.toLocaleString()})</span></p>
            </div>
          </div>
        </div>
      )}

      {check.name === "schema" && d.schema && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h4 className="text-xs font-semibold text-muted-foreground mb-3">Schema</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            {Object.entries(d.schema).map(([k, v]) => (
              <div key={k}>
                <p className="text-xs text-muted-foreground">{k}</p>
                <p className="font-mono text-info mt-0.5">{String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw JSON */}
      <CodeBlock data={d} title="Raw Details" />
    </div>
  );
};

export const ChecksPage = () => {
  const r = getRuntimeReport();
  const checks = r.checks;
  const passed = checks.filter(c => c.status === "ok").length;
  const warnings = checks.filter(c => c.status === "warning").length;
  const errors = checks.filter(c => c.status === "error").length;
  const [activeCheck, setActiveCheck] = useState(checks[0].name);
  const currentCheck = checks.find(c => c.name === activeCheck)!;

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total Checks" value={checks.length} icon={Activity} variant="info" />
        <StatCard label="Passed" value={passed} icon={CheckCircle} variant="success" />
        <StatCard label="Warnings" value={warnings} icon={AlertTriangle} variant="warning" />
        <StatCard label="Errors" value={errors} icon={XCircle} variant="error" />
      </div>

      {/* Check tabs */}
      <div className="overflow-x-auto scrollbar-thin">
        <div className="flex gap-1 p-1 rounded-lg border border-border bg-surface-2 min-w-max">
          {checks.map(c => (
            <button
              key={c.name}
              onClick={() => setActiveCheck(c.name)}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                activeCheck === c.name
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${
                c.status === "ok" ? "bg-success" : c.status === "warning" ? "bg-warning" : "bg-error"
              }`} />
              {c.name.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Active check detail */}
      <CheckDetail check={currentCheck} />
    </div>
  );
};
