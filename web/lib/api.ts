import {
  ApiError,
  ContainersResponse,
  DiagnoseResponse,
  LogsResponse,
  MenuResponse,
  NarrateResponse,
  StatsResponse,
} from "./types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(res.status, detail);
  }

  return res.json();
}

export function getContainers() {
  return request<ContainersResponse>("/api/containers");
}

export function getLogs(name: string, tail = 100) {
  return request<LogsResponse>(`/api/containers/${name}/logs?tail=${tail}`);
}

export function getStats(name: string) {
  return request<StatsResponse>(`/api/containers/${name}/stats`);
}

export function getMenu(name: string) {
  return request<MenuResponse>(`/api/containers/${name}/menu`);
}

export function diagnose(name: string, commandKey: string) {
  return request<DiagnoseResponse>(`/api/containers/${name}/diagnose`, {
    method: "POST",
    body: JSON.stringify({ command_key: commandKey }),
  });
}

export function narrate(name: string) {
  return request<NarrateResponse>(`/api/containers/${name}/narrate`, {
    method: "POST",
  });
}
