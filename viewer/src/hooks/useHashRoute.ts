import { useCallback, useEffect, useState } from "react";
import { findPlace, places } from "@/data/places";
import type { ModelVersionId } from "@/data/types";

export type Route = { slug: string; version: ModelVersionId };

const toHash = (r: Route) => `#${r.slug}/${r.version}`;

/** Unknown slug -> first place; version the place lacks -> its first version. */
function resolve(slug: string, version: string): Route {
  const place = findPlace(slug) ?? places[0];
  return { slug: place.slug, version: (place.versions.find((v) => v.id === version) ?? place.versions[0]).id };
}

function parse(): Route {
  const [slug = "", version = ""] = decodeURIComponent(window.location.hash.slice(1)).split("/");
  const route = resolve(slug, version);
  // canonicalise shared links such as #forums-palace/master (no master yet) in place
  if (window.location.hash && window.location.hash !== toHash(route)) window.history.replaceState(null, "", toHash(route));
  return route;
}

/** Deep links: #amir-temur, #forums-palace/yandex. */
export function useHashRoute() {
  const [route, setRoute] = useState<Route>(parse);

  useEffect(() => {
    const onChange = () => setRoute(parse());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const go = useCallback((next: Route, push: boolean) => {
    setRoute(next);
    if (push) window.location.hash = toHash(next);
    else window.history.replaceState(null, "", toHash(next));
  }, []);

  return { route, selectPlace: (slug: string) => go(resolve(slug, ""), true), selectVersion: (version: ModelVersionId) => go({ ...route, version }, false) };
}
