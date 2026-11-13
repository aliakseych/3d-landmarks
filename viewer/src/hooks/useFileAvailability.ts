import { useEffect, useState } from "react";

/** Checks with HEAD requests which files exist. A static host's HTML fallback counts as missing. */
export function useFileAvailability(urls: string[]): Record<string, boolean | undefined> {
  const [available, setAvailable] = useState<Record<string, boolean | undefined>>({});
  const key = urls.join("|");

  useEffect(() => {
    let live = true;
    setAvailable({});
    for (const url of urls) {
      fetch(url, { method: "HEAD" })
        .then((r) => r.ok && !(r.headers.get("content-type") ?? "").includes("text/html"))
        .catch(() => false)
        .then((ok) => live && setAvailable((prev) => ({ ...prev, [url]: ok })));
    }
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return available;
}
