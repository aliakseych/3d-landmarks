#!/usr/bin/env python3
"""Check a Yandex Maps 3D submission model against the tech requirements.

usage: validate.py <model.glb|obj|fbx-not-supported> [--max-tris 15000]
Checks: triangle count, single closed shell (watertight, no holes from below),
consistent outward winding (positive volume), flat base, no textures/UVs/materials.
Exit 1 on any FAIL.
"""
import json, struct, sys
import numpy as np
import trimesh

path = sys.argv[1]
max_tris = int(sys.argv[sys.argv.index("--max-tris") + 1]) if "--max-tris" in sys.argv else 15000
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


if path.endswith(".glb"):
    raw = open(path, "rb").read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    gj = json.loads(raw[20:20 + jlen])
    check(not gj.get("images") and not gj.get("textures"), "no images/textures in glTF")
    check(not gj.get("materials"), "no materials in glTF")
    attrs = {k for m in gj["meshes"] for p in m["primitives"] for k in p["attributes"]}
    check(not any(a.startswith(("TEXCOORD", "COLOR")) for a in attrs), f"no UV/colour attributes ({sorted(attrs)})")
mesh = trimesh.load(path, force="mesh", process=False)
mesh.merge_vertices()  # glTF splits verts at sharp normals; weld for topology checks
t = len(mesh.faces)
check(t <= max_tris, f"triangles {t} <= {max_tris}")
check(mesh.is_watertight, "watertight (closed from every side incl. bottom)")
check(mesh.is_winding_consistent, "consistent winding")
check(mesh.volume > 0, f"outward normals (signed volume {mesh.volume:.2f} m^3 > 0)")
bodies = mesh.split(only_watertight=False)
check(len(bodies) == 1, f"single shell ({len(bodies)} bodies)")
up = 1 if path.endswith((".glb", ".obj")) else 2  # glTF/OBJ exported Y-up
v = mesh.vertices
lo = v[:, up].min()
base = v[np.abs(v[:, up] - lo) < 1e-4]
check(abs(lo) < 1e-3 and len(base) >= 3, f"flat base at height 0 ({len(base)} verts on plane, min {lo:.4f})")
ext = mesh.extents
print(f"INFO extents (x, up, z) = {np.round(ext, 2).tolist()} m; area {mesh.area:.1f} m^2")
sys.exit(1 if fails else 0)
