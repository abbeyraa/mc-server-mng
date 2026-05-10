"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { profilesApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface Profile {
  id: number;
  name: string;
  minecraft_version: string;
  server_type: string;
  world_name: string;
  ram_min: string;
  ram_max: string;
  is_active: boolean;
}

export default function ProfilesPage() {
  const router = useRouter();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchProfiles();
  }, [router]);

  async function fetchProfiles() {
    const res = await profilesApi.list();
    setProfiles(res.data);
  }

  async function activate(id: number) {
    setLoading(true);
    try {
      await profilesApi.activate(id);
      alert("Profile activation queued. Server will restart.");
      await fetchProfiles();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this profile?")) return;
    await profilesApi.remove(id);
    await fetchProfiles();
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Server Profiles</h1>
      {profiles.length === 0 && <p className="text-gray-400">No profiles yet.</p>}
      <div className="grid gap-4">
        {profiles.map((p) => (
          <div
            key={p.id}
            className={`bg-mc-panel border rounded-lg p-5 flex items-center justify-between ${
              p.is_active ? "border-mc-green" : "border-mc-border"
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{p.name}</span>
                {p.is_active && (
                  <span className="text-xs bg-mc-green text-white px-2 py-0.5 rounded">ACTIVE</span>
                )}
              </div>
              <p className="text-sm text-gray-400 mt-1">
                {p.server_type} {p.minecraft_version} · World: {p.world_name} · RAM: {p.ram_min}–{p.ram_max}
              </p>
            </div>
            <div className="flex gap-2">
              {!p.is_active && (
                <button
                  onClick={() => activate(p.id)}
                  disabled={loading}
                  className="px-3 py-1 bg-mc-green text-white rounded text-sm disabled:opacity-50"
                >
                  Activate
                </button>
              )}
              <button
                onClick={() => remove(p.id)}
                className="px-3 py-1 bg-red-700 text-white rounded text-sm hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
