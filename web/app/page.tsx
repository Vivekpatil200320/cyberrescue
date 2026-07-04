"use client";

import { useEffect, useState } from "react";
import { getContainers } from "@/lib/api";
import { ContainerSummary } from "@/lib/types";
import ContainerCard from "@/components/ContainerCard";

export default function DashboardPage() {
  const [containers, setContainers] = useState<ContainerSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await getContainers();
        if (!cancelled) {
          setContainers(res.containers);
          setError(null);
        }
      } catch {
        if (!cancelled) setError("Couldn't reach the backend. It may be waking up — try again shortly.");
      }
    }

    load();
    const interval = setInterval(load, 10_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <header className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">CyberRescue</h1>
        <p className="mt-3 text-gray-600">
          A live demo of the CyberRescue MCP server — real Docker log/stats/exec calls against 3
          intentionally broken containers, safely sandboxed to this fixed demo set. No arbitrary
          containers, no freeform shell input.{" "}
          <a
            href="https://github.com/vivekpatil200320/cyberrescue"
            className="font-medium text-blue-600 underline"
          >
            View source on GitHub
          </a>
          .
        </p>
      </header>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {!containers && !error && <p className="text-sm text-gray-500">Loading containers…</p>}

      {containers && (
        <div className="grid gap-4 sm:grid-cols-2">
          {containers.map((c) => (
            <ContainerCard key={c.name} container={c} />
          ))}
        </div>
      )}
    </main>
  );
}
