import { ContainerState } from "@/lib/types";

const STYLES: Record<ContainerState, string> = {
  running: "bg-accent/10 text-accent border-accent/30",
  exited: "bg-destructive/10 text-destructive border-destructive/30",
  restarting: "bg-warning/10 text-warning border-warning/30",
  not_found: "bg-surface text-muted-foreground border-border",
  unknown: "bg-surface text-muted-foreground border-border",
};

const DOT_STYLES: Record<ContainerState, string> = {
  running: "bg-accent",
  exited: "bg-destructive",
  restarting: "bg-warning",
  not_found: "bg-muted-foreground",
  unknown: "bg-muted-foreground",
};

export default function StatusBadge({ state }: { state: ContainerState }) {
  const isLive = state === "running" || state === "restarting";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-wide ${STYLES[state] ?? STYLES.unknown}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${DOT_STYLES[state] ?? DOT_STYLES.unknown} ${isLive ? "animate-pulse" : ""}`}
      />
      {state}
    </span>
  );
}
