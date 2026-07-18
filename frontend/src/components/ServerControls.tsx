"use client";
import { useState } from "react";
import { serverApi } from "@/lib/api";

interface Props {
  status: string;
  eulaAccepted: boolean | null;
  onAction: () => void;
}

export default function ServerControls({ status, eulaAccepted, onAction }: Props) {
  const [loading, setLoading] = useState(false);

  async function act(fn: () => Promise<unknown>) {
    setLoading(true);
    try {
      await fn();
      onAction();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Action failed";
      alert(msg);
    } finally {
      setLoading(false);
    }
  }

  const running = status === "running";
  const stopped = status === "stopped" || status === "crashed";

  return (
    <div className="flex gap-3">
      <button
        disabled={!stopped || loading || eulaAccepted === false}
        onClick={() => act(serverApi.start)}
        className="px-4 py-2 bg-mc-green text-white rounded disabled:opacity-40 hover:bg-green-600 transition"
      >
        Start
      </button>
      {eulaAccepted === false && (
        <button
          disabled={loading}
          onClick={() => act(serverApi.acceptEula)}
          className="px-4 py-2 bg-yellow-500 text-white rounded disabled:opacity-40 hover:bg-yellow-600 transition"
        >
          Accept EULA
        </button>
      )}
      <button
        disabled={!running || loading}
        onClick={() => act(serverApi.stop)}
        className="px-4 py-2 bg-red-600 text-white rounded disabled:opacity-40 hover:bg-red-700 transition"
      >
        Stop
      </button>
      <button
        disabled={!running || loading}
        onClick={() => act(serverApi.restart)}
        className="px-4 py-2 bg-yellow-500 text-white rounded disabled:opacity-40 hover:bg-yellow-600 transition"
      >
        Restart
      </button>
    </div>
  );
}
