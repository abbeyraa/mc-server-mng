import axios, { type AxiosProgressEvent } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: `${API_BASE}/api/v1` });

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("mc_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("mc_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

// Typed helpers
export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/login", { username, password }),
  me: () => api.get("/auth/me"),
};

export const serverApi = {
  status: () => api.get("/server/status"),
  start: () => api.post("/server/start"),
  acceptEula: () => api.post("/server/eula"),
  stop: () => api.post("/server/stop"),
  restart: () => api.post("/server/restart"),
};

export const playitApi = {
  get: () => api.get("/playit"),
  update: (domain: string) => api.put("/playit", { domain }),
  attach: () => api.post("/playit/attach"),
  detach: () => api.delete("/playit/attach"),
};

export const profilesApi = {
  list: () => api.get("/profiles"),
  create: (data: unknown) => api.post("/profiles", data),
  update: (id: number, data: unknown) => api.put(`/profiles/${id}`, data),
  remove: (id: number) => api.delete(`/profiles/${id}`),
  activate: (id: number) => api.post(`/profiles/${id}/activate`),
};

export const jarsApi = {
  list: () => api.get("/jars"),
  upload: (file: File, onUploadProgress?: (event: AxiosProgressEvent) => void) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/jars/upload", fd, { onUploadProgress });
  },
  uploadBatch: (files: File[], onUploadProgress?: (event: AxiosProgressEvent) => void) => {
    const fd = new FormData();
    files.forEach((file) => fd.append("files", file));
    return api.post("/jars/upload-batch", fd, { onUploadProgress });
  },
  remove: (filename: string) => api.delete(`/jars/${filename}`),
};

export const worldsApi = {
  list: () => api.get("/worlds"),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/worlds/upload", fd);
  },
  select: (world_name: string, profile_id: number) =>
    api.post("/worlds/select", { world_name, profile_id }),
  remove: (name: string) => api.delete(`/worlds/${name}`),
};

export const modsApi = {
  list: (profile_id?: number) => api.get("/mods", { params: { profile_id } }),
  upload: (file: File, profile_id?: number) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/mods/upload", fd, { params: { profile_id } });
  },
  toggle: (filename: string, enabled: boolean, profile_id?: number) =>
    api.post("/mods/toggle", { filename, enabled }, { params: { profile_id } }),
  remove: (filename: string, profile_id?: number) =>
    api.delete(`/mods/${filename}`, { params: { profile_id } }),
};

export const backupApi = {
  list: () => api.get("/backup"),
  create: (profile_id?: number) => api.post("/backup", { profile_id }),
  restore: (backup_id: number) => api.post("/backup/restore", { backup_id }),
  downloadUrl: (backup_id: number) => `${API_BASE}/api/v1/backup/${backup_id}/download`,
};

export const metricsApi = {
  get: () => api.get("/metrics"),
};

export const consoleApi = {
  command: (command: string) => api.post("/console/command", { command }),
};
