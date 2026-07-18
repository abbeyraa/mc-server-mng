"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { jarsApi, profilesApi } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

interface Profile {
  id: number;
  name: string;
  minecraft_version: string;
  server_type: string;
  jar_path: string;
  world_name: string;
  ram_min: string;
  ram_max: string;
  java_args: string[];
  mods_path: string | null;
  is_active: boolean;
  jar_exists: boolean;
}

interface Jar {
  filename: string;
  path: string;
  minecraft_version?: string | null;
  server_type?: string | null;
}

interface ProfileForm {
  name: string;
  minecraft_version: string;
  server_type: string;
  jar_path: string;
  world_name: string;
  ram_min: string;
  ram_max: string;
  java_args: string;
}

const emptyForm: ProfileForm = {
  name: "",
  minecraft_version: "1.20.1",
  server_type: "vanilla",
  jar_path: "",
  world_name: "",
  ram_min: "1G",
  ram_max: "4G",
  java_args: "",
};

function worldNameFromProfile(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "") || "world";
}

export default function ProfilesPage() {
  const router = useRouter();
  const jarRef = useRef<HTMLInputElement>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [jars, setJars] = useState<Jar[]>([]);
  const [form, setForm] = useState<ProfileForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) router.push("/login");
    else fetchAll();
  }, [router]);

  async function fetchAll() {
    const [profileRes, jarRes] = await Promise.all([
      profilesApi.list(),
      jarsApi.list(),
    ]);
    setProfiles(profileRes.data);
    setJars(jarRes.data);
    const firstJar = jarRes.data[0];
    setForm((current) => ({
      ...current,
      jar_path: current.jar_path || firstJar?.path || "",
      minecraft_version: current.jar_path ? current.minecraft_version : firstJar?.minecraft_version || current.minecraft_version,
      server_type: current.jar_path ? current.server_type : firstJar?.server_type || current.server_type,
    }));
  }

  function update<K extends keyof ProfileForm>(key: K, value: ProfileForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function selectJar(path: string) {
    const jar = jars.find((item) => item.path === path);
    setForm((current) => ({
      ...current,
      jar_path: path,
      minecraft_version: jar?.minecraft_version || current.minecraft_version,
      server_type: jar?.server_type || current.server_type,
    }));
  }

  function edit(profile: Profile) {
    setEditingId(profile.id);
    setForm({
      name: profile.name,
      minecraft_version: profile.minecraft_version,
      server_type: profile.server_type,
      jar_path: profile.jar_path,
      world_name: profile.world_name,
      ram_min: profile.ram_min,
      ram_max: profile.ram_max,
      java_args: profile.java_args.join("\n"),
    });
  }

  function resetForm() {
    setEditingId(null);
    setForm({
      ...emptyForm,
      jar_path: jars[0]?.path || "",
    });
  }

  async function uploadJar() {
    const files = Array.from(jarRef.current?.files ?? []);
    const jarFiles = files.filter((file) => file.name.endsWith(".jar"));
    if (files.length > 0 && jarFiles.length !== files.length) {
      alert("Only .jar files are allowed.");
    }
    if (jarFiles.length === 0) return;

    setUploading(true);
    setUploadProgress(0);
    setUploadStatus(`Uploading ${jarFiles.length} jar${jarFiles.length === 1 ? "" : "s"}...`);
    try {
      if (jarFiles.length === 1) {
        await jarsApi.upload(jarFiles[0], (event) => {
          if (event.total) setUploadProgress(Math.round((event.loaded / event.total) * 100));
        });
      } else {
        await jarsApi.uploadBatch(jarFiles, (event) => {
          if (event.total) setUploadProgress(Math.round((event.loaded / event.total) * 100));
        });
      }
      setUploadProgress(100);
      setUploadStatus(`Uploaded ${jarFiles.length} jar${jarFiles.length === 1 ? "" : "s"}.`);
      if (jarRef.current) jarRef.current.value = "";
      await fetchAll();
    } catch (e: unknown) {
      setUploadStatus("");
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to upload jar");
    } finally {
      setUploading(false);
    }
  }

  async function removeJar(filename: string) {
    if (!confirm(`Delete jar "${filename}"?`)) return;
    await jarsApi.remove(filename);
    await fetchAll();
  }

  async function saveProfile() {
    if (!form.jar_path) {
      alert("Upload/select a server jar first.");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        ...form,
        world_name: form.world_name || worldNameFromProfile(form.name),
        java_args: form.java_args.split("\n").map((arg) => arg.trim()).filter(Boolean),
        mods_path: editingId ? profiles.find((p) => p.id === editingId)?.mods_path ?? null : null,
      };
      if (editingId) await profilesApi.update(editingId, payload);
      else await profilesApi.create(payload);
      resetForm();
      await fetchAll();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to save profile");
    } finally {
      setLoading(false);
    }
  }

  async function activate(id: number) {
    setLoading(true);
    try {
      await profilesApi.activate(id);
      alert("Profile activated and server restarted.");
      await fetchAll();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this profile?")) return;
    try {
      await profilesApi.remove(id);
      await fetchAll();
    } catch (e: unknown) {
      alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to delete profile");
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Server Profiles</h1>
        <div className="flex gap-2">
          <input ref={jarRef} type="file" accept=".jar" multiple className="hidden" onChange={uploadJar} />
          <button disabled={uploading} onClick={() => jarRef.current?.click()} className="px-4 py-2 bg-mc-green text-white rounded text-sm disabled:opacity-50">
            {uploading ? "Uploading..." : "Upload Jar"}
          </button>
        </div>
      </div>

      {(uploading || uploadStatus) && (
        <div className="bg-mc-panel border border-mc-border rounded-lg p-4">
          <div className="flex items-center justify-between gap-3 text-sm text-gray-300">
            <span>{uploadStatus}</span>
            <span className="font-mono">{uploadProgress}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded bg-mc-dark">
            <div className="h-full bg-mc-green transition-all" style={{ width: `${uploadProgress}%` }} />
          </div>
        </div>
      )}

      <div className="bg-mc-panel border border-mc-border rounded-lg p-5 space-y-4">
        <h2 className="text-lg font-semibold">{editingId ? "Edit Profile" : "Create Profile"}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-gray-300">Name<input value={form.name} onChange={(e) => update("name", e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border" /></label>
          <label className="text-sm text-gray-300">Minecraft Version<input value={form.minecraft_version} onChange={(e) => update("minecraft_version", e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border" /></label>
          <label className="text-sm text-gray-300">Server Type<select value={form.server_type} onChange={(e) => update("server_type", e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border"><option value="vanilla">Vanilla</option><option value="fabric">Fabric</option><option value="forge">Forge</option><option value="paper">Paper</option><option value="spigot">Spigot</option></select></label>
          <label className="text-sm text-gray-300">Server Jar<select value={form.jar_path} onChange={(e) => selectJar(e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border"><option value="">Select jar</option>{jars.map((jar) => <option key={jar.path} value={jar.path}>{jar.filename}{jar.minecraft_version ? ` (${jar.minecraft_version})` : ""}</option>)}</select></label>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm text-gray-300">RAM Min<input value={form.ram_min} onChange={(e) => update("ram_min", e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border" /></label>
            <label className="text-sm text-gray-300">RAM Max<input value={form.ram_max} onChange={(e) => update("ram_max", e.target.value)} className="mt-1 w-full rounded bg-mc-dark border-mc-border" /></label>
          </div>
        </div>
        <label className="block text-sm text-gray-300">Java Args<textarea value={form.java_args} onChange={(e) => update("java_args", e.target.value)} rows={4} className="mt-1 w-full rounded bg-mc-dark border-mc-border" placeholder="-XX:+UseG1GC" /></label>
        <div className="flex flex-wrap gap-2">
          <button disabled={loading} onClick={saveProfile} className="px-4 py-2 bg-mc-green text-white rounded disabled:opacity-50">{editingId ? "Save Changes" : "Create Profile"}</button>
          {editingId && <button onClick={resetForm} className="px-4 py-2 bg-mc-border text-white rounded">Cancel</button>}
        </div>
      </div>

      {jars.length > 0 && (
        <div className="bg-mc-panel border border-mc-border rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-3">Uploaded Jars</h2>
          <div className="grid gap-2">
            {jars.map((jar) => (
              <div key={jar.filename} className="flex items-center justify-between text-sm">
                <span>{jar.filename}{jar.minecraft_version ? ` · ${jar.minecraft_version}` : ""}{jar.server_type ? ` · ${jar.server_type}` : ""}</span>
                <button onClick={() => removeJar(jar.filename)} className="px-3 py-1 bg-red-700 text-white rounded hover:bg-red-600">Delete</button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {profiles.map((p) => (
          <div key={p.id} className={`bg-mc-panel border rounded-lg p-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between ${p.is_active ? "border-mc-green" : "border-mc-border"}`}>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{p.name}</span>
                {p.is_active && <span className="text-xs bg-mc-green text-white px-2 py-0.5 rounded">ACTIVE</span>}
                {!p.jar_exists && <span className="text-xs bg-red-700 text-white px-2 py-0.5 rounded">JAR MISSING</span>}
              </div>
              <p className="text-sm text-gray-400 mt-1">{p.server_type} {p.minecraft_version} · World: {p.world_name} · RAM: {p.ram_min}-{p.ram_max}</p>
              <p className="text-xs text-gray-500 mt-1">Jar: {p.jar_path}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => edit(p)} className="px-3 py-1 bg-mc-border text-white rounded text-sm">Edit</button>
              {!p.is_active && <button onClick={() => activate(p.id)} disabled={loading} className="px-3 py-1 bg-mc-green text-white rounded text-sm disabled:opacity-50">Activate</button>}
              <button onClick={() => remove(p.id)} disabled={p.is_active && p.jar_exists} className="px-3 py-1 bg-red-700 text-white rounded text-sm disabled:opacity-40 hover:bg-red-600">Delete</button>
            </div>
          </div>
        ))}
        {profiles.length === 0 && <p className="text-gray-400">No profiles yet.</p>}
      </div>
    </div>
  );
}
