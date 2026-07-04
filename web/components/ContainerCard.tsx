import Link from "next/link";
import { ContainerSummary } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function ContainerCard({ container }: { container: ContainerSummary }) {
  return (
    <Link
      href={`/containers/${container.name}`}
      className="group block cursor-pointer rounded-xl border border-border bg-surface p-5 transition-all duration-200 hover:border-accent/50 hover:bg-surface-muted focus-visible:border-accent/50"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="truncate font-mono text-base font-medium text-foreground">
          {container.name}
        </h3>
        <StatusBadge state={container.state} />
      </div>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        {container.description}
      </p>
      <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent transition-transform duration-200 group-hover:translate-x-0.5">
        Debug this container
        <span aria-hidden="true">&rarr;</span>
      </span>
    </Link>
  );
}
