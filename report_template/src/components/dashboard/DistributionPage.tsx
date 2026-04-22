import { useState } from "react";
import { getRuntimeReport } from "@/data/runtimeReport";
import { CodeBlock } from "./CodeBlock";
import { BarChart as BarChartIcon, Code } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";

type ViewMode = "graph" | "json";

const DistChart = ({
  data,
  barColor,
  totalSamples,
}: {
  data: { name: string; count: number }[];
  barColor: string;
  totalSamples: number;
}) => {
  const chartWidth = Math.max(data.length * 50, 400);
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <div style={{ width: chartWidth, minWidth: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={28}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="name"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              axisLine={false} tickLine={false}
              interval={0}
              angle={-35}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: "hsl(var(--surface-2))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "hsl(var(--foreground))" }}
              formatter={(value: number) => [
                `${value.toLocaleString()} (${((value / totalSamples) * 100).toFixed(1)}%)`,
                "Count"
              ]}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]} label={{ position: "top", fill: "hsl(var(--muted-foreground))", fontSize: 10 }}>
              {data.map((_, i) => (
                <Cell key={i} fill={barColor} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const DistributionPage = () => {
  const r = getRuntimeReport();
  const classData = Object.entries(r.class_counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
  const splitData = Object.entries(r.split_counts).map(([name, count]) => ({ name, count }));
  const totalSamples = r.total_samples;
  const [viewMode, setViewMode] = useState<ViewMode>("graph");

  return (
    <div className="space-y-6">
      {/* Toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Data Distribution</h2>
        <div className="flex items-center gap-1 rounded-lg border border-border bg-surface-2 p-0.5">
          <button
            onClick={() => setViewMode("graph")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              viewMode === "graph" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BarChartIcon className="w-3.5 h-3.5" /> Graph
          </button>
          <button
            onClick={() => setViewMode("json")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              viewMode === "json" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Code className="w-3.5 h-3.5" /> JSON
          </button>
        </div>
      </div>

      {/* Class Distribution */}
      <div className="rounded-lg border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Class Distribution</h3>
          <span className="text-xs text-muted-foreground">{classData.length} classes • {totalSamples.toLocaleString()} total</span>
        </div>
        {viewMode === "graph" ? (
          <DistChart data={classData} barColor="hsl(var(--primary))" totalSamples={totalSamples} />
        ) : (
          <CodeBlock data={r.class_counts} title="class_counts" />
        )}
      </div>

      {/* Split Distribution */}
      <div className="rounded-lg border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Split Distribution</h3>
          <span className="text-xs text-muted-foreground">{splitData.length} splits</span>
        </div>
        {viewMode === "graph" ? (
          <DistChart data={splitData} barColor="hsl(var(--success))" totalSamples={totalSamples} />
        ) : (
          <CodeBlock data={r.split_counts} title="split_counts" />
        )}
      </div>
    </div>
  );
};
