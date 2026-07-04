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

  async function run(key: string) {
    setActiveKey(key);
    setResult(null);
    setError(null);
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
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        {commands.map((cmd) => (
          <button
            key={cmd.key}
            onClick={() => run(cmd.key)}
            disabled={activeKey === cmd.key && !result && !error}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            {cmd.label}
          </button>
        ))}
      </div>

      {activeKey && !result && !error && (
        <p className="mt-3 text-sm text-gray-500">Running {activeKey}…</p>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="mt-3 space-y-2">
          <pre className="max-h-60 overflow-auto rounded-md bg-gray-950 p-4 text-xs text-gray-100">
            {result.stdout || "(no stdout)"}
          </pre>
          {result.stderr && (
            <pre className="max-h-40 overflow-auto rounded-md bg-red-950 p-4 text-xs text-red-100">
              {result.stderr}
            </pre>
          )}
          <p className="text-xs text-gray-500">
            exit code {result.exit_code}
            {result.timed_out ? " (timed out)" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
