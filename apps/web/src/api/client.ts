export type Project = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  latest_version: number | null;
  web_url?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  turn_id?: string | null;
  job_id?: string | null;
};

export type Job = {
  id: string;
  project_id: string;
  kind?: string | null;
  source?: "agent" | "manual" | "template" | "system" | null;
  turn_id?: string | null;
  status: "pending" | "running" | "succeeded" | "failed";
  phase?: string | null;
  prompt?: string | null;
  message: string | null;
  version: number | null;
  stl_ready?: boolean;
  error?: string | null;
  validation_warnings?: string[];
  web_url?: string | null;
  created_at: string;
  updated_at: string;
};

export type VersionStatus = "pending" | "complete";

export type ModelVersion = {
  version: number;
  status: VersionStatus;
  stl_url: string | null;
  parts_url: string | null;
  forge_url: string | null;
  cad_backend?: string | null;
  created_at: string;
  prompt: string | null;
  turn_id?: string | null;
  job_id?: string | null;
  validation_warnings?: string[];
  plan_summary?: string | null;
  plan_strategy?: string | null;
  plan_template_id?: string | null;
  plan_assumptions?: string[];
  plan_modules?: string[];
  review_status?: string | null;
  review_notes?: string[];
  design_revision?: number | null;
  src_files?: string[];
  forge_sources_url?: string | null;
};

export type WebChatMode = "agent" | "setup_required";

export type Health = {
  status: string;
  forgecad_available: boolean;
  cad_backend?: string;
  web_base_url?: string;
  web_turn?: "off" | "bridge" | "gateway";
  web_turn_ready?: boolean;
  web_chat_mode?: WebChatMode;
};

export type AgentRun = {
  provider: string;
  session_id: string;
  run_id: string;
  status: string;
  external_url?: string | null;
};

export type Turn = {
  turn_id?: string | null;
  routing: "agent" | "blocked";
  reason?: string | null;
  agent?: AgentRun | null;
  assistant_message_id?: string | null;
};

export type DesignPhase =
  | "intake"
  | "plan"
  | "author"
  | "render"
  | "review"
  | "done"
  | "blocked";

export type DesignTurn = {
  id: string;
  agent_phase: "running" | "replied" | "failed";
  render_phase: "idle" | "running" | "done" | "failed";
  design_phase?: DesignPhase;
  user_message_id: string;
  assistant_message_id?: string | null;
  job_id?: string | null;
  version?: number | null;
  revision?: number;
  plan_summary?: string | null;
  plan_strategy?: string | null;
  plan_template_id?: string | null;
  plan_assumptions?: string[];
  plan_modules?: string[];
  review_status?: string | null;
  review_notes?: string[];
};

export type AgentStatus = {
  active: boolean;
  turn_id?: string | null;
  provider?: string | null;
  session_id?: string | null;
  run_id?: string | null;
  status?: string | null;
  external_url?: string | null;
  active_job_id?: string | null;
};

export type ProjectCapabilities = {
  web_chat_mode: WebChatMode;
  web_turn?: string;
  assistant_ready: boolean;
};

export type ProjectState = {
  project: Project;
  messages: ChatMessage[];
  active_turn: DesignTurn | null;
  active_job: Job | null;
  agent: AgentStatus;
  capabilities: ProjectCapabilities;
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

export const listProjects = () => request<Project[]>("/api/projects");

export const createProject = (name: string) =>
  request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

export const renderForge = (
  projectId: string,
  forgeCode: string,
  label?: string,
  source: "manual" | "agent" = "manual",
  files?: Record<string, string>,
) =>
  request<Job>(`/api/projects/${projectId}/render-forge`, {
    method: "POST",
    body: JSON.stringify({
      forge_code: forgeCode,
      label: label ?? "ForgeCAD 建模",
      source,
      ...(files && Object.keys(files).length ? { files } : {}),
    }),
  });

export const getProjectState = (projectId: string) =>
  request<ProjectState>(`/api/projects/${projectId}/state`);

/** SSE project state while Agent run is active; polling fallback. */
export async function waitAgentRun(
  projectId: string,
  onUpdate: (state: ProjectState) => void,
  pollMs = 2000,
): Promise<ProjectState> {
  let current = await getProjectState(projectId);
  onUpdate(current);
  if (!current.agent.active) return current;

  if (typeof EventSource !== "undefined") {
    const streamed = await new Promise<ProjectState | null>((resolve) => {
      let last: ProjectState | null = current;
      let settled = false;
      const source = new EventSource(
        `/api/projects/${projectId}/state/events`,
      );
      const finish = (state: ProjectState | null) => {
        if (settled) return;
        settled = true;
        source.close();
        resolve(state);
      };
      source.onmessage = (event) => {
        try {
          const state = JSON.parse(event.data) as ProjectState;
          last = state;
          onUpdate(state);
          if (!state.agent.active) finish(state);
        } catch {
          finish(last);
        }
      };
      source.onerror = () => finish(last);
    });
    if (streamed && !streamed.agent.active) return streamed;
    if (streamed) current = streamed;
  }

  while (current.agent.active) {
    await sleep(pollMs);
    current = await getProjectState(projectId);
    onUpdate(current);
  }
  return current;
}

export type ModelPick = {
  x: number;
  y: number;
  z: number;
  nx: number;
  ny: number;
  nz: number;
  label?: string | null;
  element?: string | null;
};

export const sendTurn = (
  projectId: string,
  content: string,
  pick?: ModelPick | null,
  region?: string | null,
) =>
  request<Turn>(`/api/projects/${projectId}/turn`, {
    method: "POST",
    body: JSON.stringify({
      content,
      pick: pick ?? undefined,
      region: region ?? undefined,
    }),
  });

export const getJob = (projectId: string, jobId: string) =>
  request<Job>(`/api/projects/${projectId}/jobs/${jobId}`);

const TERMINAL_JOB_STATUSES = new Set<Job["status"]>(["succeeded", "failed"]);

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** SSE push updates with polling until terminal (SSE alone can miss terminal events). */
export async function waitJob(
  projectId: string,
  initial: Job,
  onUpdate: (job: Job) => void,
  pollMs = 800,
): Promise<Job> {
  let current = initial;
  onUpdate(current);
  if (TERMINAL_JOB_STATUSES.has(current.status)) return current;

  const jobId = initial.id;

  return await new Promise<Job>((resolve) => {
    let settled = false;
    let source: EventSource | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    const finish = (job: Job) => {
      if (settled) return;
      settled = true;
      source?.close();
      if (pollTimer != null) clearInterval(pollTimer);
      resolve(job);
    };

    const apply = (job: Job) => {
      current = job;
      onUpdate(job);
      if (TERMINAL_JOB_STATUSES.has(job.status)) finish(job);
    };

    const poll = async () => {
      if (settled) return;
      try {
        apply(await getJob(projectId, jobId));
      } catch {
        // transient network errors — keep polling
      }
    };

    pollTimer = setInterval(() => void poll(), pollMs);

    if (typeof EventSource !== "undefined") {
      source = new EventSource(
        `/api/projects/${projectId}/jobs/${jobId}/events`,
      );
      source.onmessage = (event) => {
        try {
          apply(JSON.parse(event.data) as Job);
        } catch {
          source?.close();
        }
      };
      source.onerror = () => source?.close();
    }

    void poll();
  });
}

export const listActiveJobs = (projectId: string) =>
  request<Job[]>(`/api/projects/${projectId}/jobs/active`);

export const resumeVersionStl = (projectId: string, version: number) =>
  request<Job>(`/api/projects/${projectId}/versions/${version}/resume-stl`, {
    method: "POST",
  });

export const listVersions = (projectId: string) =>
  request<ModelVersion[]>(`/api/projects/${projectId}/versions`);
