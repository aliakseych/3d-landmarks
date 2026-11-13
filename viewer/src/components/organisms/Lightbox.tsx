import { useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import type { Photo } from "@/data/types";
import { IconButton } from "@/components/atoms/IconButton";
import { PhotoCredit } from "@/components/molecules/PhotoCredit";

type Props = { photos: Photo[]; index: number; onIndex: (i: number) => void; onClose: () => void };

/** Modal photo viewer on a native <dialog>: focus trap and Esc come from the platform. */
export function Lightbox({ photos, index, onIndex, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const photo = photos[index];
  const prev = () => onIndex((index - 1 + photos.length) % photos.length);
  const next = () => onIndex((index + 1) % photos.length);

  useEffect(() => {
    const d = dialog.current;
    if (d && !d.open) d.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      aria-label="Photo viewer"
      onClose={onClose}
      onClick={(e) => e.target === dialog.current && onClose()}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") prev();
        if (e.key === "ArrowRight") next();
      }}
      className="m-0 h-dvh max-h-none w-screen max-w-none bg-transparent p-0 backdrop:bg-black/85"
    >
      <div className="flex h-full flex-col items-center justify-center gap-3 p-3 sm:p-8" onClick={(e) => e.target === e.currentTarget && onClose()}>
        <div className="absolute right-3 top-3 sm:right-6 sm:top-6">
          <IconButton label="Close" onClick={onClose} autoFocus>
            <X className="size-5" />
          </IconButton>
        </div>
        <img src={photo.src} alt={photo.caption} className="min-h-0 max-w-full flex-1 rounded-lg object-contain" />
        <div className="flex w-full max-w-3xl items-center gap-3 rounded-xl bg-card p-3">
          <IconButton label="Previous photo" onClick={prev}>
            <ChevronLeft className="size-5" />
          </IconButton>
          <div className="min-w-0 flex-1 text-center">
            <p className="text-sm font-medium">
              {photo.caption} <span className="font-normal text-muted-foreground">({index + 1}/{photos.length})</span>
            </p>
            <PhotoCredit photo={photo} />
          </div>
          <IconButton label="Next photo" onClick={next}>
            <ChevronRight className="size-5" />
          </IconButton>
        </div>
      </div>
    </dialog>
  );
}
