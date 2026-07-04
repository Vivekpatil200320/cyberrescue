"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getLogs, getMenu, getStats } from "@/lib/api";
import { ApiError, LogsResponse, MenuCommand, StatsResponse } from "@/lib/types";
import LogViewer from "@/components/LogViewer";
import DiagnosticMenu from "@/components/DiagnosticMenu";
import NarrativePanel from "@/components/NarrativePanel";

function SectionSkeleton({ heightClass = "h-24" }: { heightClass?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg border border-border bg-surface-muted ${heightClass}`}
    />
  );
}

export default function ContainerDebugPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);

  const [logs, setLogs] = useState<LogsResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [menu, setMenu] = useState<MenuCommand[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statsChecked, setStatsChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [logsRes, menuRes] = await Promise.all([getLogs(name), getMenu(name)]);
        if (cancelled) return;
        setLogs(logsRes);
        setMenu(menuRes.commands);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 429) {
          setError("Rate limited — please wait a moment and refresh.");
        } else {
          setError("Couldn't load this container. It may not be running.");
        }
      }

      try {
        const statsRes = await getStats(name);
        if (!cancelled) setStats(statsRes);
      } catch {
        // Stats require a running container — a stopped demo container is
        // itself informative, so we just leave the stats panel empty.
      } finally {
        if (!cancelled) setStatsChecked(true);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [name]);

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16 sm:py-20">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-accent"
      >
        <span aria-hidden="true">&larr;</span> Back to dashboard
      </Link>
      <h1 className="mt-5 font-mono text-2xl font-semibold text-foreground">{name}</h1>

      {error && (
        <p className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      )}

      <section className="mt-10">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Logs
        </h2>
        {logs ? <LogViewer logs={logs} /> : !error && <SectionSkeleton heightClass="h-40" />}
      </section>

      {statsChecked && stats && (
        <section className="mt-10">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Memory / CPU
          </h2>
          <div className="grid grid-cols-3 gap-3 rounded-lg border border-border bg-surface p-4">
            <div>
              <div className="text-xs text-muted-foreground">CPU</div>
              <div className="mt-1 font-mono text-lg tabular-nums text-foreground">
                {stats.cpu_percent}%
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Memory</div>
              <div className="mt-1 font-mono text-lg tabular-nums text-foreground">
                {stats.memory_mb}
                <span className="text-sm text-muted-foreground"> / {stats.memory_limit_mb} MB</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Memory %</div>
              <div className="mt-1 font-mono text-lg tabular-nums text-foreground">
                {stats.memory_percent}%
              </div>
            </div>
          </div>
        </section>
      )}

      {menu && menu.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Diagnostics
          </h2>
          <DiagnosticMenu containerName={name} commands={menu} />
        </section>
      )}

      <section className="mt-10">
        <NarrativePanel containerName={name} />
      </section>
    </main>
  );
}
