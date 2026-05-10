"use client";
import { useMetrics } from "@/hooks/useMetrics";

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm text-gray-400 mb-1">
        <span>{label}</span>
        <span>{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-mc-border rounded">
        <div
          className="h-2 bg-mc-green rounded transition-all duration-300"
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

export default function MetricsPanel() {
  const { metrics, connected } = useMetrics();

  if (!connected) return <p className="text-gray-500 text-sm">Connecting to metrics...</p>;
  if (!metrics) return <p className="text-gray-500 text-sm">Waiting for data...</p>;

  return (
    <div className="space-y-4">
      <Bar label="CPU" value={metrics.cpu_percent} />
      <Bar label={`RAM (${metrics.ram_used_mb} / ${metrics.ram_total_mb} MB)`} value={metrics.ram_percent} />
      <Bar label={`Disk (${metrics.disk_used_gb} / ${metrics.disk_total_gb} GB)`} value={metrics.disk_percent} />
      {metrics.uptime_seconds != null && (
        <p className="text-sm text-gray-400">
          Uptime: {Math.floor(metrics.uptime_seconds / 60)}m {Math.floor(metrics.uptime_seconds % 60)}s
        </p>
      )}
    </div>
  );
}
