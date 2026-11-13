import { Download } from "lucide-react";
import type { ModelVersion } from "@/data/types";
import { cn } from "@/lib/utils";

type Props = { versions: ModelVersion[]; availability: Record<string, boolean | undefined> };

/** Download links for every file of every version; missing files are shown as unavailable. */
export function DownloadList({ versions, availability }: Props) {
  return (
    <div className="flex flex-col gap-4">
      {versions.map((v) => (
        <div key={v.id}>
          <p className="mb-2 text-sm font-medium">{v.label}</p>
          <ul className="flex flex-wrap gap-2">
            {v.files.map((f) => {
              const ok = availability[f.url];
              const missing = ok === false;
              return (
                <li key={f.url}>
                  <a
                    href={missing ? undefined : f.url}
                    download
                    aria-disabled={missing || ok === undefined}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-medium transition",
                      missing || ok === undefined ? "pointer-events-none opacity-50" : "hover:border-accent hover:text-accent",
                    )}
                  >
                    <Download className="size-4" aria-hidden="true" />
                    {f.format}
                    {missing && <span className="text-xs font-normal text-muted-foreground">unavailable</span>}
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
