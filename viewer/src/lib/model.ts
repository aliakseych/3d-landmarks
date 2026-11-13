import { Box3, Mesh, Vector3, type Group } from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export type ModelStats = {
  triangles: number;
  vertices: number;
  /** Bounding-box size in metres: x = east-west, y = height, z = north-south */
  size: Vector3;
  center: Vector3;
  minY: number;
  radius: number;
};

export type LoadedModel = { url: string; scene: Group; bytes: number; stats: ModelStats };

type Entry = {
  promise: Promise<LoadedModel>;
  listeners: Set<(progress: number | null) => void>;
  last: number | null;
};

const entries = new Map<string, Entry>();

/** Fetches and parses a GLB once. Failed loads are not cached, so files that appear later can be retried. */
export function loadModel(url: string, onProgress: (progress: number | null) => void): { promise: Promise<LoadedModel>; unsubscribe: () => void } {
  let entry = entries.get(url);
  if (!entry) {
    const created: Entry = { listeners: new Set(), last: 0, promise: undefined as unknown as Promise<LoadedModel> };
    created.promise = fetchModel(url, (p) => {
      created.last = p;
      created.listeners.forEach((l) => l(p));
    }).catch((err) => {
      entries.delete(url);
      throw err;
    });
    entries.set(url, created);
    entry = created;
  }
  entry.listeners.add(onProgress);
  onProgress(entry.last);
  const target = entry;
  return { promise: entry.promise, unsubscribe: () => target.listeners.delete(onProgress) };
}

async function fetchModel(url: string, onProgress: (progress: number | null) => void): Promise<LoadedModel> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`The file is not available (HTTP ${res.status}).`);
  const total = Number(res.headers.get("content-length")) || 0;
  const reader = res.body?.getReader();
  if (!reader) throw new Error("Streaming is not supported by this browser.");

  const chunks: Uint8Array[] = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    onProgress(total ? Math.min(received / total, 1) : null);
  }
  const buffer = new Uint8Array(received);
  let offset = 0;
  for (const c of chunks) {
    buffer.set(c, offset);
    offset += c.length;
  }
  const magic = String.fromCharCode(...buffer.slice(0, 4));
  if (magic !== "glTF") throw new Error("The file is not available (the server returned something other than a GLB).");

  const gltf = await new GLTFLoader().parseAsync(buffer.buffer, "");
  const scene = gltf.scene;
  return { url, scene, bytes: received, stats: measure(scene) };
}

function measure(scene: Group): ModelStats {
  let triangles = 0;
  let vertices = 0;
  scene.updateMatrixWorld(true);
  scene.traverse((obj) => {
    if (!(obj instanceof Mesh)) return;
    const geo = obj.geometry;
    const position = geo.getAttribute("position");
    vertices += position.count;
    triangles += (geo.index ? geo.index.count : position.count) / 3;
    if (!geo.getAttribute("normal")) geo.computeVertexNormals();
  });
  const box = new Box3().setFromObject(scene);
  const size = box.getSize(new Vector3());
  const center = box.getCenter(new Vector3());
  return { triangles, vertices, size, center, minY: box.min.y, radius: size.length() / 2 };
}
