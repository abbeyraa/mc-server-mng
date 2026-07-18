"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { modsApi, profilesApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface Mod {
  filename: string;
  size_bytes: number;
  enabled: boolean;
}

interface Profile {
  id: number;
  name: string;
  server_type: string;
  is_active: boolean;
}

function formatSize(bytes: number): string {
  if (bytes > 1024 * 1024) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function ModsPage() {
  const router = useRouter();
  const [mods, setMods] = useState<Mod[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number | "">("");
  const [restartRequired, setRestartRequired] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchProfiles();
  }, [router]);

  useEffect(() => {
    if (selectedProfileId) fetchMods(Number(selectedProfileId));
  }, [selectedProfileId]);

  async function fetchProfiles() {
    const res = await profilesApi.list();
    setProfiles(res.data);
    setSelectedProfileId(res.data.find((p: Profile) => p.is_active)?.id || res.data[0]?.id || "");
  }

  async function fetchMods(profileId: number) {
    const res = await modsApi.list(profileId);
    setMods(res.data);
  }

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file || !selectedProfileId) return;
    await modsApi.upload(file, Number(selectedProfileId));
    if (fileRef.current) fileRef.current.value = "";
    setRestartRequired(true);
    await fetchMods(Number(selectedProfileId));
  }

  async function toggle(filename: string, enabled: boolean) {
    if (!selectedProfileId) return;
    await modsApi.toggle(filename, !enabled, Number(selectedProfileId));
    setRestartRequired(true);
    await fetchMods(Number(selectedProfileId));
  }

  async function remove(filename: string) {
    if (!selectedProfileId || !confirm(`Delete mod "${filename}"?`)) return;
    await modsApi.remove(filename, Number(selectedProfileId));
    setRestartRequired(true);
    await fetchMods(Number(selectedProfileId));
  }

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId);
  const moddedServer = selectedProfile?.server_type === "forge" || selectedProfile?.server_type === "fabric";

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Mods</h1>
          {selectedProfile && <p className="text-sm text-gray-400 mt-1">Profile: {selectedProfile.name}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={selectedProfileId} onChange={(e) => { setSelectedProfileId(e.target.value ? Number(e.target.value) : ""); setRestartRequired(false); }} className="rounded bg-mc-panel border-mc-border text-sm">
            <option value="">Select profile</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>{profile.name}{profile.is_active ? " (active)" : ""}</option>
            ))}
          </select>
          <input ref={fileRef} type="file" accept=".jar" className="hidden" onChange={upload} />
          <button onClick={() => fileRef.current?.click()} disabled={!selectedProfileId} className="px-4 py-2 bg-mc-green text-white rounded text-sm disabled:opacity-40">
            Upload Mod (.jar)
          </button>
        </div>
      </div>

      {selectedProfile && !moddedServer && (
        <div className="bg-yellow-950/50 border border-yellow-700 text-yellow-100 rounded-lg p-4 text-sm">
          This profile is {selectedProfile.server_type}. Mods normally require a Forge or Fabric profile.
        </div>
      )}
      {restartRequired && (
        <div className="bg-mc-panel border border-mc-green text-green-100 rounded-lg p-4 text-sm">
          Restart required for mod changes to take effect.
        </div>
      )}

      <div className="grid gap-3">
        {mods.map((m) => (
          <div key={m.filename} className="bg-mc-panel border border-mc-border rounded-lg p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <span className="font-medium">{m.filename}</span>
              <span className={`ml-3 text-xs px-2 py-0.5 rounded ${m.enabled ? "bg-mc-green text-white" : "bg-gray-700 text-gray-300"}`}>
                {m.enabled ? "Enabled" : "Disabled"}
              </span>
              <p className="text-sm text-gray-400 mt-1">{formatSize(m.size_bytes)}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => toggle(m.filename, m.enabled)} className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-500">
                {m.enabled ? "Disable" : "Enable"}
              </button>
              <button onClick={() => remove(m.filename)} className="px-3 py-1 bg-red-700 text-white rounded text-sm hover:bg-red-600">
                Delete
              </button>
            </div>
          </div>
        ))}
        {selectedProfileId && mods.length === 0 && <p className="text-gray-400">No mods uploaded for this profile.</p>}
        {!selectedProfileId && <p className="text-gray-400">Create or select a profile first.</p>}
      </div>
    </div>
  );
}
