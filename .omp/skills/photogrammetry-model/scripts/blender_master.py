"""Blender headless: level, georeference, crop and export the textured master model.

blender -b -P blender_master.py -- <model.obj> <georef.json> <outDir> [options]
  --analyze              print radial z-profile + render raw aligned views, no export
  --center X,Y           statue axis in ENU metres (default: auto from upper half)
  --radius R             keep geometry within R metres of the axis (default: keep all)
  --base-z Z             cut everything below Z and cap flat (default: mesh min z)
  --sky L                delete faces whose texture luminance > L (sky/cloud membranes)
  --sky-above Z          ...only faces whose centre is above Z (protect bright stone below)
  --max-z Z              cut everything above Z
  --sky-tint L           recolour bright (> L) statue faces above --sky-above and all fill faces
                         with the statue's median texel (hides sky bleed on unobserved tops)
  --base-snap D          snap base-loop verts within D m of --base-z onto it (default 0.2)
  --keep-frac F          keep islands with >= F x main-island verts (default 0.02)
  --fill-holes N         close open boundary loops up to N edges (base cap is always closed)
  --tris N               decimate to N triangles (default: keep)
  --tex N                max texture size in GLB (default 4096)
  --name NAME            output basename (default: model)
  --photos DIR           display-oriented JPEGs -> photo-vs-render overlays
  --overlay a,b,c        photo stems for overlays (default: 6 spread over the ring)
Outputs in outDir: NAME.glb (textured, Y-up, metres, origin = base centre),
NAME_aligned.obj (+mtl/texture, Z-up, for downstream tools), NAME.json (geo meta),
renders/*.png.
"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_utils as ru  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
obj_path, georef_path, out_dir = argv[:3]
opts = argv[3:]


def opt(name, default=None, cast=str):
    if name in opts:
        return cast(opts[opts.index(name) + 1])
    return default


analyze = "--analyze" in opts
name = opt("--name", "model")
os.makedirs(os.path.join(out_dir, "renders"), exist_ok=True)
geo = json.load(open(georef_path))
M = Matrix(geo["matrix"])

ru.reset_scene()
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis="Y", up_axis="Z")
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.context.view_layer.objects.active = objs[0]
for o in objs:
    o.select_set(True)
if len(objs) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
me = ob.data
me.transform(M)
if me.has_custom_normals:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()  # stale after the similarity transform
me.update()

co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
zmin, zmax = co[:, 2].min(), co[:, 2].max()
up = co[co[:, 2] > zmin + 0.5 * (zmax - zmin)]
auto_c = np.median(up[:, :2], axis=0)
cx, cy = (map(float, opt("--center").split(",")) if opt("--center") else auto_c)
r = np.hypot(co[:, 0] - cx, co[:, 1] - cy)
print(f"verts={len(co)} z=[{zmin:.2f},{zmax:.2f}] auto_center=({auto_c[0]:.2f},{auto_c[1]:.2f})")
print("   z     n   r50   r95  rmax")
step = max((zmax - zmin) / 40, 0.05)
for z0 in np.arange(zmin, zmax, step):
    m = (co[:, 2] >= z0) & (co[:, 2] < z0 + step)
    if m.sum():
        rr = r[m]
        print(f"{z0:6.2f} {m.sum():5d} {np.percentile(rr,50):5.2f} {np.percentile(rr,95):5.2f} {rr.max():5.2f}")

if analyze:
    ru.add_lights_world()
    ru.render_turntable(ob, os.path.join(out_dir, "renders", "raw"), textured=True, n=4)
    sys.exit(0)

def islands_of(bm):
    for v in bm.verts:
        v.tag = False
    out = []
    for v in bm.verts:
        if v.tag:
            continue
        v.tag = True
        stack, comp = [v], []
        while stack:
            a = stack.pop(); comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if not b.tag:
                    b.tag = True; stack.append(b)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def face_luminance(bm, me, size=2048):
    """Texture luminance (stored sRGB values) at each face's UV centroid."""
    img = next(n.image for m in me.materials if m and m.node_tree for n in m.node_tree.nodes
               if n.type == "TEX_IMAGE" and n.image and "norm" not in n.image.name.lower())
    small = img.copy(); small.scale(size, size)
    px = np.empty(size * size * 4, np.float32); small.pixels.foreach_get(px)
    bpy.data.images.remove(small)
    px = px.reshape(size, size, 4)  # row 0 = bottom (v=0)
    uvl = bm.loops.layers.uv.active
    lum = {}
    for f in bm.faces:
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops)
        v = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        r, g, b, _ = px[min(int(v * size), size - 1), min(int(u * size), size - 1)]
        lum[f] = 0.299 * r + 0.587 * g + 0.114 * b
    return lum


bm = bmesh.new(); bm.from_mesh(me)
R = opt("--radius", None, float)
if R:
    kill = [v for v in bm.verts if math.hypot(v.co.x - cx, v.co.y - cy) > R]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
# Object Capture leaves unwelded slits; weld so they become fillable holes
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
# sky/tree membranes: Object Capture fuses bright sky behind the statue into sheets
sky = opt("--sky", None, float)
if sky is not None:
    above = opt("--sky-above", -1e9, float)
    lum = face_luminance(bm, me)
    kill = [f for f in bm.faces if lum[f] > sky and f.calc_center_median().z > above]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    print(f"sky faces removed: {len(kill)}")
top = opt("--max-z", None, float)
if top is not None:
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, top),
                           plane_no=(0, 0, 1), clear_outer=True)
base_z = opt("--base-z", None, float)
if base_z is not None:
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, base_z),
                           plane_no=(0, 0, 1), clear_inner=True)
# drop floating islands (ground scraps, membrane leftovers)
keep_frac = opt("--keep-frac", 0.02, float)
isl = islands_of(bm)
for comp in isl[1:]:
    if len(comp) < keep_frac * len(isl[0]):
        bmesh.ops.delete(bm, geom=comp, context="VERTS")
print(f"islands={len(isl)} sizes={[len(c) for c in isl[:6]]}")

def orient_like_neighbours(bm, new):
    """Flip new faces whose winding disagrees with an adjacent old face (keeps source winding)."""
    newset, flip = set(new), []
    for f in new:
        for l in f.loops:
            o = l.link_loop_radial_next
            if o is not l and o.face not in newset:
                if o.vert is l.vert:  # same direction along the shared edge -> inconsistent
                    flip.append(f)
                break
    bmesh.ops.reverse_faces(bm, faces=flip)
    return new


def fill_loops(bm, edges, sides):
    return orient_like_neighbours(bm, bmesh.ops.holes_fill(bm, edges=edges, sides=sides)["faces"])


def fan_fill(bm, edges):
    """Close boundary loops holes_fill rejects: split into closed walks, fan from the centroid."""
    left, new = set(edges), []
    while left:
        e0 = left.pop(); start, cur = e0.verts; walk = [start, cur]
        while cur is not start:
            nxt = next((e for e in cur.link_edges if e in left), None)
            if nxt is None:
                walk = None; break
            left.discard(nxt); cur = nxt.other_vert(cur); walk.append(cur)
        if not walk or len(walk) < 4:
            continue
        ring = walk[:-1]
        c = bm.verts.new(sum((v.co for v in ring), Vector()) / len(ring))
        for a, b in zip(ring, ring[1:] + ring[:1]):
            new.append(bm.faces.new((a, b, c)))
    return orient_like_neighbours(bm, new)


def boundary_loops(bm):
    edges = {e for e in bm.edges if e.is_boundary}
    loops = []
    while edges:
        stack, comp = [edges.pop()], []
        while stack:
            e = stack.pop(); comp.append(e)
            for v in e.verts:
                for e2 in v.link_edges:
                    if e2 in edges:
                        edges.discard(e2); stack.append(e2)
        loops.append(comp)
    return loops


# cap the flat base: boundary loops touching the cut plane get their low verts snapped onto it
if base_z is None:
    base_z = min(v.co.z for v in bm.verts)
snap = opt("--base-snap", 0.2, float)
new_faces = []
for lp in boundary_loops(bm):
    vs = {v for e in lp for v in e.verts}
    if any(abs(v.co.z - base_z) < 1e-3 for v in vs):
        for v in vs:
            if v.co.z - base_z < snap:
                v.co.z = base_z
        new_faces += fill_loops(bm, lp, 0)
print(f"base cap faces: {len(new_faces)}")
fill = opt("--fill-holes", 0, int)
if fill:
    f = fill_loops(bm, [e for e in bm.edges if e.is_boundary], fill)
    f += fan_fill(bm, [e for lp in boundary_loops(bm) if len(lp) <= fill for e in lp])
    new_faces += f
    print(f"filled holes: {len(f)} faces")
print(f"open boundary edges left: {sum(1 for e in bm.edges if e.is_boundary)}")
# unobserved tops get sky texels from grazing views: retint bright statue faces and all fill
# faces with one representative statue texel
tint = opt("--sky-tint", None, float)
if tint is not None:
    above = opt("--sky-above", -1e9, float)
    lum = face_luminance(bm, me)
    uvl = bm.loops.layers.uv.active
    newset = set(new_faces)
    statue = [f for f in bm.faces if f not in newset and f.calc_center_median().z > above]
    med = float(np.median([lum[f] for f in statue]))
    ref = min(statue, key=lambda f: abs(lum[f] - med) + (0 if f.calc_area() > 1e-4 else 1))
    ref_uv = sum((l[uvl].uv for l in ref.loops), Vector((0, 0))) / len(ref.loops)
    bright = [f for f in statue if lum[f] > tint] + new_faces
    for f in bright:
        for l in f.loops:
            l[uvl].uv = ref_uv
    print(f"retinted faces: {len(bright)} (statue median lum {med:.3f})")
bm.to_mesh(me); bm.free()

# origin = base centre on the axis
me.transform(Matrix.Translation((-cx, -cy, -base_z)))
me.update()
lat = geo["lat0"] + math.degrees(cy / 6378137.0)
lon = geo["lon0"] + math.degrees(cx / (6378137.0 * math.cos(math.radians(geo["lat0"]))))

tris = opt("--tris", None, int)
ntri = sum(len(p.vertices) - 2 for p in me.polygons)
if tris and ntri > tris:
    mod = ob.modifiers.new("dec", "DECIMATE"); mod.ratio = tris / ntri
    bpy.ops.object.modifier_apply(modifier=mod.name)
ntri = sum(len(p.vertices) - 2 for p in me.polygons)
for p in me.polygons:
    p.use_smooth = True
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
dims = [float(x) for x in co.max(0) - co.min(0)]
print(f"final tris={ntri} dims(E,N,Up)={dims}")

# texture downscale for the app GLB (keeps the source image for the aligned OBJ)
tex = opt("--tex", 4096, int)
for img in bpy.data.images:
    if img.size[0] > tex:
        img.scale(tex, tex)
glb = os.path.join(out_dir, f"{name}.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_image_format="JPEG",
                          export_jpeg_quality=90, export_yup=True, export_apply=True)
bpy.ops.wm.obj_export(filepath=os.path.join(out_dir, f"{name}_aligned.obj"), forward_axis="Y",
                      up_axis="Z", export_materials=True, path_mode="COPY", export_normals=True)
meta = dict(name=name, lat=lat, lon=lon, base_centre_enu=[cx, cy, base_z], triangles=ntri,
            dimensions_m=dict(east_west=dims[0], north_south=dims[1], height=dims[2]),
            axes="glTF: +Y up, -Z north, +X east; OBJ_aligned: Z up, +Y north, +X east; metres",
            scale_rel_err=geo["scale_rel_err"], heading_gps_vs_compass_deg=geo["gps_vs_compass_deg"],
            georef=os.path.basename(georef_path))
json.dump(meta, open(os.path.join(out_dir, f"{name}.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))

ru.add_lights_world()
ru.render_turntable(ob, os.path.join(out_dir, "renders", name), textured=True, n=8)
photos = opt("--photos")
if photos:
    cams = geo["cameras"]
    stems = opt("--overlay", None)
    stems = stems.split(",") if stems else [k[:-5] for k in sorted(cams)][:: max(1, len(cams) // 6)]
    shift = Matrix.Translation((-cx, -cy, -base_z)) @ M
    ru.render_photo_overlays(ob, geo, shift, photos, stems, os.path.join(out_dir, "renders"))
