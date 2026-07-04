import { ContainerState } from "@/lib/types";

const STYLES: Record<ContainerState, string> = {
  running: "bg-green-100 text-green-800 border-green-300",
  exited: "bg-red-100 text-red-800 border-red-300",
  restarting: "bg-amber-100 text-amber-800 border-amber-300",
  not_found: "bg-gray-100 text-gray-700 border-gray-300",
  unknown: "bg-gray-100 text-gray-700 border-gray-300",
};

export default function StatusBadge({ state }: { state: ContainerState }) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium ${STYLES[state] ?? STYLES.unknown}`}
    >
      {state}
    </span>
  );
}
