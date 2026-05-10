"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { worldsApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface World {
  name: string;
  size_bytes: number;
  is_active: boolean;
}

function formatSize(bytes: number): string {
  if (bytes > 1024 * 1024 * 1024) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes > 1024 * 1024) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function WorldsPage() {
  const router = useRouter();
  const [worlds, setWorlds] = useState<World[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetch();
  }, [router]);

  async function fetch() {
    const res = await worldsApi.list();
    setWorlds(res.data);
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    await worldsApi.upload(file);
    await fetch();
  }

  async function remove(name: string) {
    if (!confirm(`Delete world "${name}"? This cannot be undone.`)) return;
    await worldsApi.remove(name);
    await fetch();
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Worlds</h1>
        <div className="flex gap-2">
          <input ref={fileRef} type="file" accept=".zip" className="hidden" onChange={upload} />
          <button
            onClick={() => fileRef.current?.click()}
            className="px-4 py-2 bg-mc-green text-white rounded text-sm"
          >
            Upload World (.zip)
          </button>
        </div>
      </div>
      <div className="grid gap-3">
        {worlds.map((w) => (
          <div
            key={w.name}
            className={`bg-mc-panel border rounded-lg p-4 flex items-center justify-between ${
              w.is_active ? "border-mc-green" : "border-mc-border"
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{w.name}</span>
                {w.is_active && (
                  <span className="text-xs bg-mc-green text-white px-2 py-0.5 rounded">ACTIVE</span>
                )}
              </div>
              <p className="text-sm text-gray-400">{formatSize(w.size_bytes)}</p>
            </div>
            <button
              onClick={() => remove(w.name)}
              disabled={w.is_active}
              className="px-3 py-1 bg-red-700 text-white rounded text-sm disabled:opacity-40"
            >
              Delete
            </button>
          </div>
        ))}
        {worlds.length === 0 && <p className="text-gray-400">No worlds found.</p>}
      </div>
    </div>
  );
}
