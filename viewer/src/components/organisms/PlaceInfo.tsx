import { ExternalLink, MapPin } from "lucide-react";
import type { Place } from "@/data/types";
import { FactList } from "@/components/molecules/FactList";

export function PlaceInfo({ place }: { place: Place }) {
  const { lat, lon, address, yandexMapsUrl } = place.location;
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="flex flex-col gap-4 text-base leading-relaxed">
        {place.description.map((p) => (
          <p key={p.slice(0, 24)}>{p}</p>
        ))}
        <div className="text-sm text-muted-foreground">
          <p className="mb-1 font-medium text-foreground">Sources</p>
          <ul className="flex flex-col gap-0.5">
            {place.sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline decoration-border underline-offset-2 hover:text-foreground">
                  {s.label} <ExternalLink className="size-3" aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="flex flex-col gap-4">
        <FactList facts={place.facts} />
        <a
          href={yandexMapsUrl}
          target="_blank"
          rel="noreferrer"
          className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 transition hover:border-accent"
        >
          <MapPin className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden="true" />
          <span className="min-w-0 text-sm">
            <span className="block font-medium">Open in Yandex Maps</span>
            <span className="block text-muted-foreground">{address}</span>
            <span className="block tabular-nums text-muted-foreground">{lat.toFixed(5)}, {lon.toFixed(5)}</span>
          </span>
        </a>
      </div>
    </div>
  );
}
