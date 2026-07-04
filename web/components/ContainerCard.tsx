import Link from "next/link";
import { ContainerSummary } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function ContainerCard({ container }: { container: ContainerSummary }) {
  return (
    <Link
      href={`/containers/${container.name}`}
      className="block rounded-lg border border-gray-200 p-5 transition hover:border-gray-400 hover:shadow-sm"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-mono text-lg font-semibold">{container.name}</h3>
        <StatusBadge state={container.state} />
      </div>
      <p className="mt-2 text-sm text-gray-600">{container.description}</p>
      <span className="mt-4 inline-block text-sm font-medium text-blue-600">
        Debug this container &rarr;
      </span>
    </Link>
  );
}
