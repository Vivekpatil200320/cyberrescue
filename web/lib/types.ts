export type ContainerState = "running" | "exited" | "restarting" | "not_found" | "unknown";

export interface ContainerSummary {
  name: string;
  state: ContainerState;
  description: string;
}

export interface ContainersResponse {
  containers: ContainerSummary[];
}

export interface LogsResponse {
  container_id: string;
  log_lines: string[];
  line_count: number;
  truncated: boolean;
}

export interface StatsResponse {
  cpu_percent: number;
  memory_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
  processes?: string[];
}

export interface MenuCommand {
  key: string;
  label: string;
}

export interface MenuResponse {
  commands: MenuCommand[];
}

export interface DiagnoseResponse {
  stdout: string;
  stderr: string;
  exit_code: number;
  timed_out: boolean;
}

export interface NarrateResponse {
  container: string;
  narrative: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
