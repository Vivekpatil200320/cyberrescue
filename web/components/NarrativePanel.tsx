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
    <div className="rounded-xl border border-accent/20 bg-gradient-to-br from-accent/[0.06] to-transparent p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 font-medium text-foreground">
          <span className="text-accent" aria-hidden="true">
            ✦
          </span>
          AI Root-Cause Diagnosis
        </h3>
        <button
          onClick={generate}
          disabled={loading}
          className="cursor-pointer rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground transition-opacity duration-150 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Generate AI diagnosis"}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      {text && (
        <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-foreground/90">
          {text}
        </p>
      )}
    </div>
  );
}
