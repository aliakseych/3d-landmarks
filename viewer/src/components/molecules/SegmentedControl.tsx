import { cn } from "@/lib/utils";

export type Segment<T extends string> = { value: T; label: string; short?: string; disabled?: boolean; note?: string };

type Props<T extends string> = {
  label: string;
  value: T;
  options: Segment<T>[];
  onChange: (value: T) => void;
  className?: string;
};

/** Single-choice radio group styled as a pill switcher. */
export function SegmentedControl<T extends string>({ label, value, options, onChange, className }: Props<T>) {
  return (
    <div role="radiogroup" aria-label={label} className={cn("flex w-full gap-1 rounded-full border border-border bg-muted/70 p-1 sm:inline-flex sm:w-auto", className)}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-label={o.note ? `${o.label} (${o.note})` : o.label}
            aria-checked={active}
            disabled={o.disabled}
            onClick={() => onChange(o.value)}
            className={cn(
              "min-w-0 flex-1 whitespace-nowrap rounded-full px-2 sm:flex-none sm:px-3.5 py-1.5 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent",
              active ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
              o.disabled && "cursor-not-allowed opacity-40 hover:text-muted-foreground",
            )}
          >
            {o.short ? <><span className="sm:hidden">{o.short}</span><span className="hidden sm:inline">{o.label}</span></> : o.label}
            {o.note && <span className="ml-1.5 hidden sm:inline text-xs text-muted-foreground">{o.note}</span>}
          </button>
        );
      })}
    </div>
  );
}
