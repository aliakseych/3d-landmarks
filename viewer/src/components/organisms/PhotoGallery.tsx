import { useState } from "react";
import type { Place } from "@/data/types";
import { PhotoCredit } from "@/components/molecules/PhotoCredit";
import { Lightbox } from "./Lightbox";

export function PhotoGallery({ place }: { place: Place }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="flex flex-col gap-4">
      <ul className="grid gap-4 sm:grid-cols-2">
        {place.photos.map((p, i) => (
          <li key={p.src} className="flex min-w-0 flex-col gap-1.5">
            <button
              type="button"
              onClick={() => setOpen(i)}
              aria-label={`Open photo: ${p.caption}`}
              className="group aspect-[4/3] w-full overflow-hidden rounded-xl border border-border bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              <img src={p.src} alt={p.caption} loading="lazy" className="size-full object-cover transition duration-300 group-hover:scale-105" />
            </button>
            <PhotoCredit photo={p} />
          </li>
        ))}
      </ul>

      {open !== null && <Lightbox photos={place.photos} index={open} onIndex={setOpen} onClose={() => setOpen(null)} />}
    </div>
  );
}
