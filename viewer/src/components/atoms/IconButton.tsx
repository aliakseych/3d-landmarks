import type { ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/utils";

type Props = ComponentPropsWithoutRef<"button"> & { label: string; pressed?: boolean };

/** Round icon-only button. `label` is the accessible name and tooltip. */
export function IconButton({ label, pressed, className, children, ...props }: Props) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={pressed}
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-full border border-border bg-card/90 text-foreground shadow-sm backdrop-blur transition",
        "hover:bg-card focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-40",
        pressed && "border-accent bg-accent text-white hover:bg-accent",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
