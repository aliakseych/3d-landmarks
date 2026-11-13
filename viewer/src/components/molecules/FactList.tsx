import type { Fact } from "@/data/types";

export function FactList({ facts }: { facts: Fact[] }) {
  return (
    <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2">
      {facts.map((f) => (
        <div key={f.label} className="bg-card px-4 py-3">
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{f.label}</dt>
          <dd className="mt-0.5 text-sm font-medium">{f.value}</dd>
        </div>
      ))}
    </dl>
  );
}
