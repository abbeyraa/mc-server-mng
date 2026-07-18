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

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${days}d ${hours}h ${minutes}m ${secs}s`;
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
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="border border-mc-border rounded p-3">
          <p className="text-xs text-gray-400">Server PID</p>
          <p className="font-semibold">{metrics.server_pid ?? "Stopped"}</p>
        </div>
        <div className="border border-mc-border rounded p-3">
          <p className="text-xs text-gray-400">Server CPU</p>
          <p className="font-semibold">
            {metrics.server_cpu_percent == null ? "—" : `${metrics.server_cpu_percent.toFixed(1)}%`}
          </p>
        </div>
        <div className="border border-mc-border rounded p-3">
          <p className="text-xs text-gray-400">Server RAM</p>
          <p className="font-semibold">{metrics.server_ram_mb == null ? "—" : `${metrics.server_ram_mb} MB`}</p>
        </div>
      </div>
      {metrics.uptime_seconds != null && (
        <p className="text-sm text-gray-400">
          Uptime: {formatUptime(metrics.uptime_seconds)}
        </p>
      )}
    </div>
  );
}
