"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { backupApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface Backup {
  id: number;
  filename: string;
  world_name: string;
  trigger: string;
  size_bytes: number;
  created_at: string;
  profile_id: number | null;
}

function formatSize(bytes: number): string {
  if (bytes > 1024 * 1024 * 1024) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes > 1024 * 1024) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function BackupPage() {
  const router = useRouter();
  const [backups, setBackups] = useState<Backup[]>([]);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchBackups();
  }, [router]);

  async function fetchBackups() {
    const res = await backupApi.list();
    setBackups(res.data);
  }

  async function createBackup() {
    setCreating(true);
    try {
      await backupApi.create();
      await fetchBackups();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Backup failed");
    } finally {
      setCreating(false);
    }
  }

  async function restore(id: number) {
    if (!confirm("Restore this backup? The server must be stopped.")) return;
    try {
      await backupApi.restore(id);
      alert("World restored successfully.");
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Restore failed");
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Backups</h1>
        <button
          onClick={createBackup}
          disabled={creating}
          className="px-4 py-2 bg-mc-green text-white rounded text-sm disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create Backup"}
        </button>
      </div>
      <div className="grid gap-3">
        {backups.map((b) => (
          <div key={b.id} className="bg-mc-panel border border-mc-border rounded-lg p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-sm">{b.filename}</p>
              <p className="text-xs text-gray-400 mt-0.5">
                World: {b.world_name} · {formatSize(b.size_bytes)} · {b.trigger} ·{" "}
                {new Date(b.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex gap-2">
              <a
                href={backupApi.downloadUrl(b.id)}
                download
                className="px-3 py-1 bg-mc-panel border border-mc-border text-white rounded text-sm hover:border-mc-green"
              >
                Download
              </a>
              <button
                onClick={() => restore(b.id)}
                className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-500"
              >
                Restore
              </button>
            </div>
          </div>
        ))}
        {backups.length === 0 && <p className="text-gray-400">No backups yet.</p>}
      </div>
    </div>
  );
}
