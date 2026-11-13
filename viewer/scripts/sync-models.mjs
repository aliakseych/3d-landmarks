// Copies ../models/<slug>/**/*.{glb,obj,fbx,json} into public/models/.
// Generated output: never fails when models are missing (the viewer shows an unavailable state).
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const src = resolve(root, "../models");
const dest = join(root, "public/models");
const EXT = new Set([".glb", ".obj", ".fbx", ".json"]);

let copied = 0;
function walk(from, to) {
  for (const entry of readdirSync(from, { withFileTypes: true })) {
    const a = join(from, entry.name);
    const b = join(to, entry.name);
    if (entry.isDirectory()) walk(a, b);
    else if (EXT.has(extname(entry.name).toLowerCase()) && statSync(a).size > 0) {
      mkdirSync(to, { recursive: true });
      cpSync(a, b);
      copied++;
    }
  }
}

try {
  rmSync(dest, { recursive: true, force: true });
  if (existsSync(src)) walk(src, dest);
  else console.warn(`[sync-models] ${src} not found, skipping`);
  console.log(`[sync-models] copied ${copied} file(s) to public/models`);
} catch (err) {
  console.warn("[sync-models] skipped:", err.message);
}
