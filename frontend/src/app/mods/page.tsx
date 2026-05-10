"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { modsApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface Mod {
  filename: string;
  size_bytes: number;
  enabled: boolean;
}

export default function ModsPage() {
  const router = useRouter();
  const [mods, setMods] = useState<Mod[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchMods();
  }, [router]);

  async function fetchMods() {
    const res = await modsApi.list();
    setMods(res.data);
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    await modsApi.upload(file);
    await fetchMods();
  }

  async function toggle(filename: string, enabled: boolean) {
    await modsApi.toggle(filename, !enabled);
    await fetchMods();
  }

  async function remove(filename: string) {
    if (!confirm(`Delete mod "${filename}"?`)) return;
    await modsApi.remove(filename);
    await fetchMods();
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Mods</h1>
        <div>
          <input ref={fileRef} type="file" accept=".jar" className="hidden" onChange={upload} />
          <button
            onClick={() => fileRef.current?.click()}
            className="px-4 py-2 bg-mc-green text-white rounded text-sm"
          >
            Upload Mod (.jar)
          </button>
        </div>
      </div>
      <div className="grid gap-3">
        {mods.map((m) => (
          <div key={m.filename} className="bg-mc-panel border border-mc-border rounded-lg p-4 flex items-center justify-between">
            <div>
              <span className="font-medium">{m.filename}</span>
              <span className={`ml-3 text-xs px-2 py-0.5 rounded ${m.enabled ? "bg-mc-green text-white" : "bg-gray-700 text-gray-300"}`}>
                {m.enabled ? "Enabled" : "Disabled"}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => toggle(m.filename, m.enabled)}
                className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-500"
              >
                {m.enabled ? "Disable" : "Enable"}
              </button>
              <button
                onClick={() => remove(m.filename)}
                className="px-3 py-1 bg-red-700 text-white rounded text-sm hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {mods.length === 0 && <p className="text-gray-400">No mods uploaded.</p>}
      </div>
    </div>
  );
}
