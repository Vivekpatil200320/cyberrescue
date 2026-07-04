"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getLogs, getMenu, getStats } from "@/lib/api";
import { ApiError, LogsResponse, MenuCommand, StatsResponse } from "@/lib/types";
import LogViewer from "@/components/LogViewer";
import DiagnosticMenu from "@/components/DiagnosticMenu";
import NarrativePanel from "@/components/NarrativePanel";

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
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [name]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link href="/" className="text-sm text-blue-600 underline">
        &larr; Back to dashboard
      </Link>
      <h1 className="mt-4 font-mono text-2xl font-bold">{name}</h1>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <section className="mt-8">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
          Logs
        </h2>
        {logs ? <LogViewer logs={logs} /> : !error && <p className="text-sm text-gray-500">Loading…</p>}
      </section>

      {stats && (
        <section className="mt-8">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Memory / CPU
          </h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-gray-500">CPU</div>
              <div className="font-mono">{stats.cpu_percent}%</div>
            </div>
            <div>
              <div className="text-gray-500">Memory</div>
              <div className="font-mono">
                {stats.memory_mb} / {stats.memory_limit_mb} MB
              </div>
            </div>
            <div>
              <div className="text-gray-500">Memory %</div>
              <div className="font-mono">{stats.memory_percent}%</div>
            </div>
          </div>
        </section>
      )}

      {menu && menu.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Diagnostics
          </h2>
          <DiagnosticMenu containerName={name} commands={menu} />
        </section>
      )}

      <section className="mt-8">
        <NarrativePanel containerName={name} />
      </section>
    </main>
  );
}
