import { useCallback, useEffect, useState } from "react";
import { findPlace, places } from "@/data/places";
import type { ModelVersionId } from "@/data/types";

export type Route = { slug: string; version: ModelVersionId };

function parse(): Route {
  const [slug = "", version = ""] = decodeURIComponent(window.location.hash.slice(1)).split("/");
  return {
    slug: findPlace(slug) ? slug : places[0].slug,
    version: version === "yandex" ? "yandex" : "master",
  };
}

const toHash = (r: Route) => `#${r.slug}/${r.version}`;

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

  return { route, selectPlace: (slug: string) => go({ slug, version: "master" }, true), selectVersion: (version: ModelVersionId) => go({ ...route, version }, false) };
}
