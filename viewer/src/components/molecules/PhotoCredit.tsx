import type { Photo } from "@/data/types";
import { cn } from "@/lib/utils";

/** Author, licence and Commons file page of a photo, as required by CC BY / CC BY-SA. */
export function PhotoCredit({ photo, className }: { photo: Photo; className?: string }) {
  const link = "underline decoration-border underline-offset-2 hover:text-foreground";
  return (
    <p className={cn("text-xs leading-relaxed text-muted-foreground", className)}>
      Photo: {photo.author} ·{" "}
      <a className={link} href={photo.licenseUrl} target="_blank" rel="noreferrer license">
        {photo.license}
      </a>{" "}
      ·{" "}
      <a className={link} href={photo.source} target="_blank" rel="noreferrer">
        Wikimedia Commons
      </a>
    </p>
  );
}
