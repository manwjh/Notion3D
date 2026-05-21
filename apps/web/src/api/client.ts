export type Project = {
  id: string;
  name: string;
  tool?: string;
  track?: string;
  created_at: string;
  updated_at: string;
  latest_version: number | null;
  web_url?: string | null;
};

export type ToolDef = {
  id: string;
  track: string;
  title: string;
  description: string;
  available: boolean;
  sample_prompts: string[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  job_id?: string | null;
};

export type Job = {
  id: string;
  project_id: string;
  status: "pending" | "running" | "succeeded" | "failed";
  prompt?: string | null;
  message: string | null;
  version: number | null;
  preview_url?: string | null;
  preview_ready?: boolean;
  stl_ready?: boolean;
  created_at: string;
  updated_at: string;
};

export type VersionStatus = "pending" | "preview_ready" | "complete";

export type ModelVersion = {
  version: number;
  status: VersionStatus;
  stl_url: string | null;
  scad_url: string | null;
  preview_url: string | null;
  three_mf_url: string | null;
  created_at: string;
  prompt: string | null;
};

export type Health = {
  status: string;
  openscad_available: boolean;
  slicer_available: boolean;
  bambu_connect_available: boolean;
  agent_via_mcp?: boolean;
  mcp_server?: string;
  web_base_url?: string;
};

export type ActionResult = {
  ok: boolean;
  message: string;
  three_mf_url?: string | null;
  bambu_connect_url?: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail) throw new Error(json.detail);
    } catch (e) {
      if (e instanceof Error && e.message !== text) throw e;
    }
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const health = () => request<Health>("/health");

export const listTools = () => request<ToolDef[]>("/api/tools");

export const listProjects = () => request<Project[]>("/api/projects");

export const createProject = (name: string) =>
  request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name, tool: "parametric" }),
  });

export const renderScad = (projectId: string, scadCode: string, label?: string) =>
  request<Job>(`/api/projects/${projectId}/render-scad`, {
    method: "POST",
    body: JSON.stringify({ scad_code: scadCode, label: label ?? "手动编辑 SCAD" }),
  });

export const listMessages = (projectId: string) =>
  request<ChatMessage[]>(`/api/projects/${projectId}/messages`);

export type ModelPick = {
  x: number;
  y: number;
  z: number;
  nx: number;
  ny: number;
  nz: number;
  label?: string | null;
};

export const sendChat = (
  projectId: string,
  content: string,
  pick?: ModelPick | null,
  region?: string | null,
) =>
  request<Job>(`/api/projects/${projectId}/chat`, {
    method: "POST",
    body: JSON.stringify({
      content,
      pick: pick ?? undefined,
      region: region ?? undefined,
    }),
  });

export const getJob = (projectId: string, jobId: string) =>
  request<Job>(`/api/projects/${projectId}/jobs/${jobId}`);

export const listActiveJobs = (projectId: string) =>
  request<Job[]>(`/api/projects/${projectId}/jobs/active`);

export const resumeVersionStl = (projectId: string, version: number) =>
  request<Job>(`/api/projects/${projectId}/versions/${version}/resume-stl`, {
    method: "POST",
  });

export const listVersions = (projectId: string) =>
  request<ModelVersion[]>(`/api/projects/${projectId}/versions`);

export const sliceVersion = (projectId: string, version: number) =>
  request<ActionResult>(`/api/projects/${projectId}/versions/${version}/slice`, {
    method: "POST",
  });

export const printVersion = (projectId: string, version: number) =>
  request<ActionResult>(`/api/projects/${projectId}/versions/${version}/print`, {
    method: "POST",
  });
