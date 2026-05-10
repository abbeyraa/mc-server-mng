"use client";
import { useState, useCallback } from "react";
import { useWebSocket } from "./useWebSocket";

export interface Metrics {
  cpu_percent: number;
  ram_used_mb: number;
  ram_total_mb: number;
  ram_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  disk_percent: number;
  status: string;
  pid: number | null;
  uptime_seconds: number | null;
  active_profile: string | null;
}

export function useMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  const onMessage = useCallback((msg: string) => {
    try {
      setMetrics(JSON.parse(msg));
    } catch {
      // ignore malformed
    }
  }, []);

  const { connected } = useWebSocket("/ws/metrics", onMessage);
  return { metrics, connected };
}
