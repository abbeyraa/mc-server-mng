"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { serverApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import ServerControls from "@/components/ServerControls";
import MetricsPanel from "@/components/MetricsPanel";

interface ServerStatus {
  status: string;
  pid: number | null;
  uptime_seconds: number | null;
  active_profile: string | null;
}

const STATUS_COLOR: Record<string, string> = {
  running: "text-mc-green",
  stopped: "text-gray-400",
  crashed: "text-red-400",
  starting: "text-yellow-400",
  stopping: "text-yellow-400",
};

export default function DashboardPage() {
  const router = useRouter();
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
  }, [router]);

  async function fetchStatus() {
    try {
      const res = await serverApi.status();
      setServerStatus(res.data);
    } catch {
      // auth redirect handled by interceptor
    }
  }

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="bg-mc-panel border border-mc-border rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Server Status</p>
            <p className={`text-xl font-semibold capitalize ${STATUS_COLOR[serverStatus?.status ?? "stopped"]}`}>
              {serverStatus?.status ?? "—"}
            </p>
            {serverStatus?.active_profile && (
              <p className="text-sm text-gray-400 mt-1">Profile: {serverStatus.active_profile}</p>
            )}
          </div>
          {serverStatus && (
            <ServerControls status={serverStatus.status} onAction={fetchStatus} />
          )}
        </div>
      </div>

      <div className="bg-mc-panel border border-mc-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">System Metrics</h2>
        <MetricsPanel />
      </div>
    </div>
  );
}
