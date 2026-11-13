import { useEffect, useState } from "react";
import { loadModel, type LoadedModel } from "@/lib/model";

export type ModelState =
  | { status: "loading"; progress: number | null }
  | { status: "error"; message: string }
  | { status: "ready"; model: LoadedModel };

export function useModel(url: string, attempt = 0): ModelState {
  const [state, setState] = useState<ModelState>({ status: "loading", progress: 0 });

  useEffect(() => {
    let live = true;
    setState({ status: "loading", progress: 0 });
    const { promise, unsubscribe } = loadModel(url, (progress) => {
      if (live) setState((s) => (s.status === "loading" ? { status: "loading", progress } : s));
    });
    promise.then(
      (model) => live && setState({ status: "ready", model }),
      (err: unknown) => live && setState({ status: "error", message: err instanceof Error ? err.message : String(err) }),
    );
    return () => {
      live = false;
      unsubscribe();
    };
  }, [url, attempt]);

  return state;
}
