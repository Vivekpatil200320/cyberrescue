import { LogsResponse } from "@/lib/types";

export default function LogViewer({ logs }: { logs: LogsResponse | null }) {
  if (!logs) return null;

  return (
    <div>
      {logs.truncated && (
        <p className="mb-2 text-xs text-warning">
          Output truncated to the 50KB cap — showing the most recent lines.
        </p>
      )}
      <pre className="max-h-80 overflow-auto rounded-lg border border-border bg-surface-muted p-4 font-mono text-xs leading-relaxed text-foreground/90">
        {logs.log_lines.length > 0 ? logs.log_lines.join("\n") : "(no log output)"}
      </pre>
    </div>
  );
}
