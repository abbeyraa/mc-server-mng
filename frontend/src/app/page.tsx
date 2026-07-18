"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { playitApi, serverApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import ServerControls from "@/components/ServerControls";
import MetricsPanel from "@/components/MetricsPanel";

interface ServerStatus {
  status: string;
  pid: number | null;
  uptime_seconds: number | null;
  active_profile: string | null;
  eula_accepted: boolean | null;
}

interface PlayitStatus {
  domain: string;
  join_address: string;
  daemon_status: "running" | "unavailable";
  attach_status: "attached" | "detached" | "failed";
  attach_message: string;
  attach_started_at: string | null;
  service_mode: "native-systemd";
}

const STATUS_COLOR: Record<string, string> = {
  running: "text-mc-green",
  stopped: "text-gray-400",
  detached: "text-gray-400",
  crashed: "text-red-400",
  starting: "text-yellow-400",
  stopping: "text-yellow-400",
  failed: "text-red-400",
  unavailable: "text-red-400",
  unknown: "text-yellow-400",
};

export default function DashboardPage() {
  const router = useRouter();
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
  const [playitStatus, setPlayitStatus] = useState<PlayitStatus | null>(null);
  const [playitDomain, setPlayitDomain] = useState("");
  const [savingPlayit, setSavingPlayit] = useState(false);
  const [updatingAttach, setUpdatingAttach] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
  }, [router]);

  async function fetchStatus() {
    try {
      const [serverRes, playitRes] = await Promise.all([serverApi.status(), playitApi.get()]);
      setServerStatus(serverRes.data);
      setPlayitStatus(playitRes.data);
      setPlayitDomain(playitRes.data.domain);
    } catch {
      // auth redirect handled by interceptor
    }
  }

  async function savePlayitDomain() {
    setSavingPlayit(true);
    try {
      const res = await playitApi.update(playitDomain);
      setPlayitStatus(res.data);
      setPlayitDomain(res.data.domain);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } })?.response?.data?.detail;
      if (Array.isArray(msg)) {
        alert(msg[0]?.msg || "Unable to save Playit domain");
      } else {
        alert(msg || "Unable to save Playit domain");
      }
    } finally {
      setSavingPlayit(false);
    }
  }

  async function updatePlayitAttach(action: "attach" | "detach") {
    setUpdatingAttach(true);
    try {
      const res = action === "attach" ? await playitApi.attach() : await playitApi.detach();
      setPlayitStatus(res.data);
      setPlayitDomain(res.data.domain);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg || `Unable to ${action} Playit tunnel`);
    } finally {
      setUpdatingAttach(false);
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
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
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
            <ServerControls status={serverStatus.status} eulaAccepted={serverStatus.eula_accepted} onAction={fetchStatus} />
          )}
        </div>
        {serverStatus?.eula_accepted === false && (
          <p className="text-sm text-yellow-300">Minecraft EULA must be accepted before start.</p>
        )}
      </div>

      <div className="bg-mc-panel border border-mc-border rounded-lg p-6 space-y-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm text-gray-400">Playit.gg Tunnel</p>
            <p className="text-sm text-gray-400 mt-1">Daemon</p>
            <p className={`text-xl font-semibold capitalize ${STATUS_COLOR[playitStatus?.daemon_status ?? "unavailable"]}`}>
              {playitStatus?.daemon_status ?? "—"}
            </p>
            <p className="text-sm text-gray-400 mt-3">Attach</p>
            <p className={`text-xl font-semibold capitalize ${STATUS_COLOR[playitStatus?.attach_status ?? "detached"]}`}>
              {playitStatus?.attach_status ?? "—"}
            </p>
            {playitStatus?.attach_message && (
              <p className="text-sm text-gray-400 mt-1">{playitStatus.attach_message}</p>
            )}
            {playitStatus?.daemon_status === "unavailable" && (
              <p className="mt-2 font-mono text-sm text-yellow-300">sudo systemctl start playit</p>
            )}
          </div>
          <div className="flex flex-col gap-3 text-sm text-gray-400 sm:items-end sm:text-right">
            <div>
              <p>Mode: native systemd</p>
              <p>Target: 127.0.0.1:25565</p>
            </div>
            {playitStatus?.attach_status === "attached" ? (
              <button
                onClick={() => updatePlayitAttach("detach")}
                disabled={updatingAttach}
                className="rounded bg-red-600 px-4 py-2 font-medium text-white transition hover:bg-red-700 disabled:opacity-40"
              >
                {updatingAttach ? "Detaching..." : "Detach"}
              </button>
            ) : (
              <button
                onClick={() => updatePlayitAttach("attach")}
                disabled={updatingAttach || playitStatus?.daemon_status !== "running"}
                className="rounded bg-mc-green px-4 py-2 font-medium text-white transition hover:bg-green-600 disabled:opacity-40"
              >
                {updatingAttach ? "Attaching..." : "Attach Tunnel"}
              </button>
            )}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <label className="space-y-2">
            <span className="block text-sm text-gray-400">Join Domain</span>
            <input
              value={playitDomain}
              onChange={(e) => setPlayitDomain(e.target.value)}
              className="w-full rounded border border-mc-border bg-mc-bg px-3 py-2 text-white outline-none focus:border-mc-green"
              placeholder="post-stuffed.gl.joinmc.link"
            />
          </label>
          <button
            onClick={savePlayitDomain}
            disabled={savingPlayit || !playitDomain.trim() || playitDomain === playitStatus?.domain}
            className="self-end rounded bg-mc-green px-4 py-2 font-medium text-white transition hover:bg-green-600 disabled:opacity-40"
          >
            {savingPlayit ? "Saving..." : "Save"}
          </button>
        </div>

        <div className="rounded border border-mc-border bg-mc-bg px-4 py-3">
          <p className="text-sm text-gray-400">Minecraft Direct Connect</p>
          <p className="break-all font-mono text-lg text-white">{playitStatus?.join_address ?? (playitDomain || "—")}</p>
        </div>
      </div>

      <div className="bg-mc-panel border border-mc-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">System Metrics</h2>
        <MetricsPanel />
      </div>
    </div>
  );
}
