"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { profilesApi, worldsApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface World {
  name: string;
  size_bytes: number;
  is_active: boolean;
}

interface Profile {
  id: number;
  name: string;
  world_name: string;
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
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number | "">("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchAll();
  }, [router]);

  async function fetchAll() {
    const [worldRes, profileRes] = await Promise.all([worldsApi.list(), profilesApi.list()]);
    setWorlds(worldRes.data);
    setProfiles(profileRes.data);
    setSelectedProfileId((current) => current || profileRes.data.find((p: Profile) => p.is_active)?.id || profileRes.data[0]?.id || "");
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    await worldsApi.upload(file);
    if (fileRef.current) fileRef.current.value = "";
    await fetchAll();
  }

  async function useWorld(name: string) {
    if (!selectedProfileId) {
      alert("Select a profile first.");
      return;
    }
    await worldsApi.select(name, Number(selectedProfileId));
    await fetchAll();
  }

  async function remove(name: string) {
    if (!confirm(`Delete world "${name}"? This cannot be undone.`)) return;
    try {
      await worldsApi.remove(name);
      await fetchAll();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to delete world");
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Worlds</h1>
        <div className="flex flex-wrap gap-2">
          <select value={selectedProfileId} onChange={(e) => setSelectedProfileId(e.target.value ? Number(e.target.value) : "")} className="rounded bg-mc-panel border-mc-border text-sm">
            <option value="">Select profile</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>{profile.name}{profile.is_active ? " (active)" : ""}</option>
            ))}
          </select>
          <input ref={fileRef} type="file" accept=".zip" className="hidden" onChange={upload} />
          <button onClick={() => fileRef.current?.click()} className="px-4 py-2 bg-mc-green text-white rounded text-sm">
            Upload World (.zip)
          </button>
        </div>
      </div>
      <div className="grid gap-3">
        {worlds.map((w) => {
          const selectedProfile = profiles.find((p) => p.id === selectedProfileId);
          const selectedUsesWorld = selectedProfile?.world_name === w.name;
          return (
            <div key={w.name} className={`bg-mc-panel border rounded-lg p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${w.is_active ? "border-mc-green" : "border-mc-border"}`}>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{w.name}</span>
                  {w.is_active && <span className="text-xs bg-mc-green text-white px-2 py-0.5 rounded">ACTIVE</span>}
                  {selectedUsesWorld && !w.is_active && <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">SELECTED PROFILE</span>}
                </div>
                <p className="text-sm text-gray-400">{formatSize(w.size_bytes)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => useWorld(w.name)} disabled={!selectedProfileId || selectedUsesWorld} className="px-3 py-1 bg-mc-green text-white rounded text-sm disabled:opacity-40">
                  Use in Profile
                </button>
                <button onClick={() => remove(w.name)} disabled={w.is_active} className="px-3 py-1 bg-red-700 text-white rounded text-sm disabled:opacity-40">
                  Delete
                </button>
              </div>
            </div>
          );
        })}
        {worlds.length === 0 && <p className="text-gray-400">No worlds found.</p>}
      </div>
    </div>
  );
}
