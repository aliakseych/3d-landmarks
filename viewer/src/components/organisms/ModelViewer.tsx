import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AlertTriangle, Box, Gauge, Maximize2, Minimize2, Play, Pause, RotateCcw, Ruler, ZoomIn, ZoomOut, HardDrive } from "lucide-react";
import type { Place, ModelVersionId } from "@/data/types";
import { useModel } from "@/hooks/useModel";
import { useFileAvailability } from "@/hooks/useFileAvailability";
import { formatBytes, formatNumber } from "@/lib/format";
import type { CameraApi, ViewMode } from "./ModelCanvas";
import { IconButton } from "@/components/atoms/IconButton";
import { SegmentedControl } from "@/components/molecules/SegmentedControl";
import { DownloadList } from "@/components/molecules/DownloadList";
import { StatsShowcase } from "@/components/molecules/stats-showcase";
import { cn } from "@/lib/utils";

const ModelCanvas = lazy(() => import("./ModelCanvas").then((m) => ({ default: m.ModelCanvas })));

type Props = { place: Place; versionId: ModelVersionId; onVersionChange: (v: ModelVersionId) => void };

export function ModelViewer({ place, versionId, onVersionChange }: Props) {
  const version = place.versions.find((v) => v.id === versionId) ?? place.versions[0];
  const [mode, setMode] = useState<ViewMode>(version.textured ? "textured" : "clay");
  const [autoRotate, setAutoRotate] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const stage = useRef<HTMLDivElement>(null);
  const api = useRef<CameraApi | null>(null);
  const state = useModel(version.url, attempt);
  const availability = useFileAvailability(place.versions.flatMap((v) => v.files.map((f) => f.url)));

  // The low-poly file has no texture: textured mode only exists for the master.
  const effectiveMode: ViewMode = !version.textured && mode === "textured" ? "clay" : mode;
  useEffect(() => {
    setMode(version.textured ? "textured" : "clay");
  }, [version.id, version.textured, place.slug]);

  useEffect(() => {
    const onChange = () => setFullscreen(document.fullscreenElement === stage.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  const toggleFullscreen = () => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void stage.current?.requestFullscreen();
  };

  const ready = state.status === "ready" ? state.model : null;
  const size = ready?.stats.size;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="flex min-w-0 flex-col gap-3">
        <SegmentedControl
          label="Model version"
          value={version.id}
          onChange={onVersionChange}
          options={place.versions.map((v) => ({ value: v.id, label: v.label, short: v.id === "master" ? "Master" : "Yandex", note: availability[v.url] === false ? "unavailable" : undefined }))}
        />

        <div
          ref={stage}
          className={cn(
            "relative isolate overflow-hidden rounded-2xl border border-border bg-gradient-to-b from-white to-[#e9e5da]",
            fullscreen ? "h-screen rounded-none" : "h-[26rem] sm:h-[32rem] lg:h-[36rem]",
          )}
          data-viewer-status={state.status}
        >
          <Suspense fallback={null}>{ready && <ModelCanvas model={ready} mode={effectiveMode} autoRotate={autoRotate} apiRef={api} />}</Suspense>

          {state.status === "loading" && <LoadingOverlay progress={state.progress} />}
          {state.status === "error" && <ErrorOverlay name={version.label} url={version.url} message={state.message} onRetry={() => setAttempt((a) => a + 1)} />}

          {ready && (
            <>
              <div className="absolute left-3 top-3">
                <SegmentedControl
                  label="View mode"
                  value={effectiveMode}
                  onChange={setMode}
                  className="bg-card/90 backdrop-blur"
                  options={[
                    { value: "textured", label: "Textured", disabled: !version.textured },
                    { value: "clay", label: "Clay" },
                    { value: "wireframe", label: "Wireframe" },
                  ]}
                />
              </div>
              <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2">
                <IconButton label="Zoom in" onClick={() => api.current?.zoom(0.8)}>
                  <ZoomIn className="size-5" />
                </IconButton>
                <IconButton label="Zoom out" onClick={() => api.current?.zoom(1.25)}>
                  <ZoomOut className="size-5" />
                </IconButton>
                <IconButton label="Reset view" onClick={() => api.current?.reset()}>
                  <RotateCcw className="size-5" />
                </IconButton>
                <IconButton label="Auto-rotate" pressed={autoRotate} onClick={() => setAutoRotate((v) => !v)}>
                  {autoRotate ? <Pause className="size-5" /> : <Play className="size-5" />}
                </IconButton>
                {document.fullscreenEnabled && (
                  <IconButton label={fullscreen ? "Exit full screen" : "Full screen"} onClick={toggleFullscreen}>
                    {fullscreen ? <Minimize2 className="size-5" /> : <Maximize2 className="size-5" />}
                  </IconButton>
                )}
              </div>
            </>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {version.hint} Drag to orbit, scroll or pinch to zoom, right-drag or two fingers to pan.
        </p>
      </div>

      <aside className="flex min-w-0 flex-col gap-6">
        {ready ? (
          <StatsShowcase
            title="Model stats"
            subtitle={`${formatNumber(size!.x)} × ${formatNumber(size!.z)} × ${formatNumber(size!.y)} m (E–W × N–S × height)`}
            formatValue={formatNumber}
            className="gap-4"
            stats={[
              { value: ready.stats.triangles, label: "Triangles", icon: Box, max: 150000 },
              { value: ready.stats.vertices, label: "Vertices", icon: Gauge, max: 150000 },
              { value: Number(size!.y.toFixed(2)), suffix: " m", label: "Height", icon: Ruler, max: 60 },
              { value: Number((ready.bytes / 1024 / 1024).toFixed(2)), suffix: " MB", label: `File size (${formatBytes(ready.bytes)})`, icon: HardDrive, max: 10 },
            ]}
          />
        ) : (
          <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
            {state.status === "loading" ? "Stats appear once the model has loaded." : "No stats: this version is not available."}
          </p>
        )}
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Downloads</h3>
          <DownloadList versions={place.versions} availability={availability} />
        </div>
      </aside>
    </div>
  );
}

function LoadingOverlay({ progress }: { progress: number | null }) {
  const pct = progress == null ? null : Math.round(progress * 100);
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white/70 backdrop-blur-sm" role="status">
      <p className="text-sm font-medium">Loading model{pct != null ? ` ${pct}%` : "…"}</p>
      <div className="h-1.5 w-48 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full bg-accent transition-[width]", pct == null && "w-1/3 animate-pulse")} style={pct != null ? { width: `${pct}%` } : undefined} />
      </div>
    </div>
  );
}

function ErrorOverlay({ name, url, message, onRetry }: { name: string; url: string; message: string; onRetry: () => void }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/80 p-6 text-center" role="alert">
      <AlertTriangle className="size-8 text-accent" aria-hidden="true" />
      <p className="font-semibold">{name} is not available yet</p>
      <p className="max-w-sm text-sm text-muted-foreground">{message}</p>
      <code className="max-w-full truncate rounded bg-muted px-2 py-0.5 text-xs">{url}</code>
      <button type="button" onClick={onRetry} className="mt-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm font-medium hover:border-accent">
        Try again
      </button>
    </div>
  );
}
