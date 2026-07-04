"use client";

import { useState } from "react";
import { narrate } from "@/lib/api";
import { ApiError } from "@/lib/types";

export default function NarrativePanel({ containerName }: { containerName: string }) {
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setText(null);
    setError(null);
    try {
      const res = await narrate(containerName);
      setText(res.narrative);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError("Rate limited — please wait a moment before generating another diagnosis.");
      } else if (err instanceof ApiError && err.status === 503) {
        setError("AI narration isn't configured on this deployment.");
      } else {
        setError("Couldn't generate a diagnosis right now. Try again shortly.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-blue-900">AI Root-Cause Diagnosis</h3>
        <button
          onClick={generate}
          disabled={loading}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Generate AI diagnosis"}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {text && <p className="mt-3 whitespace-pre-line text-sm text-blue-950">{text}</p>}
    </div>
  );
}
