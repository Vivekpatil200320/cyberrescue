"use client";

import { useEffect, useState } from "react";
import { getContainers } from "@/lib/api";
import { ContainerSummary } from "@/lib/types";
import ContainerCard from "@/components/ContainerCard";

function CardSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <div className="h-4 w-28 rounded bg-surface-muted" />
        <div className="h-4 w-16 rounded-full bg-surface-muted" />
      </div>
      <div className="mt-4 h-3 w-full rounded bg-surface-muted" />
      <div className="mt-2 h-3 w-2/3 rounded bg-surface-muted" />
    </div>
  );
}

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
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16 sm:py-20">
      <header className="mb-12">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-muted-foreground">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          Live demo
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          CyberRescue
        </h1>
        <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
          A live demo of the CyberRescue MCP server — real Docker log, stats, and exec calls
          against 3 intentionally broken containers, safely sandboxed to this fixed demo set. No
          arbitrary containers, no freeform shell input.
        </p>
        <a
          href="https://github.com/vivekpatil200320/cyberrescue"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent transition-opacity hover:opacity-80"
        >
          View source on GitHub
          <span aria-hidden="true">↗</span>
        </a>
      </header>

      {error && (
        <p className="mb-6 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {containers
          ? containers.map((c) => <ContainerCard key={c.name} container={c} />)
          : !error && Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    </main>
  );
}
