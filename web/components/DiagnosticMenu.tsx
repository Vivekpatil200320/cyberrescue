"use client";

import { useState } from "react";
import { diagnose } from "@/lib/api";
import { ApiError, DiagnoseResponse, MenuCommand } from "@/lib/types";

export default function DiagnosticMenu({
  containerName,
  commands,
}: {
  containerName: string;
  commands: MenuCommand[];
}) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnoseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function run(key: string) {
    setActiveKey(key);
    setResult(null);
    setError(null);
    setRunning(true);
    try {
      const res = await diagnose(containerName, key);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError("Rate limited — please wait a moment before trying again.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong running this diagnostic.");
      }
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        {commands.map((cmd) => (
          <button
            key={cmd.key}
            onClick={() => run(cmd.key)}
            disabled={running && activeKey === cmd.key}
            className="cursor-pointer rounded-lg border border-border bg-surface px-3 py-1.5 text-sm font-medium text-foreground transition-colors duration-150 hover:border-accent/50 hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cmd.label}
          </button>
        ))}
      </div>

      {running && (
        <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          Running {activeKey}…
        </p>
      )}

      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      {result && (
        <div className="mt-3 space-y-2">
          <pre className="max-h-60 overflow-auto rounded-lg border border-border bg-surface-muted p-4 font-mono text-xs leading-relaxed text-foreground/90">
            {result.stdout || "(no stdout)"}
          </pre>
          {result.stderr && (
            <pre className="max-h-40 overflow-auto rounded-lg border border-destructive/30 bg-destructive/5 p-4 font-mono text-xs leading-relaxed text-destructive">
              {result.stderr}
            </pre>
          )}
          <p className="text-xs text-muted-foreground">
            exit code {result.exit_code}
            {result.timed_out ? " (timed out)" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
