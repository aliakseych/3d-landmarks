import { places } from "@/data/places";
import { SegmentedControl } from "@/components/molecules/SegmentedControl";

type Props = { slug: string; onSelect: (slug: string) => void };

export function SiteHeader({ slug, onSelect }: Props) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <a href="#" className="text-lg font-semibold tracking-tight">
          Tashkent landmarks <span className="text-accent">in 3D</span>
        </a>
        <SegmentedControl label="Place" value={slug} onChange={onSelect} options={places.map((p) => ({ value: p.slug, label: p.name.split(" \"")[0], short: p.slug === "amir-temur" ? "Amir Temur" : "Palace" }))} />
      </div>
    </header>
  );
}
