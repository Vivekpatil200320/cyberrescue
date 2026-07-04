import { LogsResponse } from "@/lib/types";

export default function LogViewer({ logs }: { logs: LogsResponse | null }) {
  if (!logs) return null;

  return (
    <div>
      {logs.truncated && (
        <p className="mb-2 text-xs text-amber-700">
          Output truncated to the 50KB cap — showing the most recent lines.
        </p>
      )}
      <pre className="max-h-80 overflow-auto rounded-md bg-gray-950 p-4 text-xs text-gray-100">
        {logs.log_lines.length > 0 ? logs.log_lines.join("\n") : "(no log output)"}
      </pre>
    </div>
  );
}
