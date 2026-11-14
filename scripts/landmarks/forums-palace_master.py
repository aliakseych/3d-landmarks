"""Textured master: Palace of International Forums "Uzbekistan" (Tashkent).

blender -b -P scripts/landmarks/forums-palace_master.py -- <outDir>
    --piece <side> <model.obj> <georef.json> [--piece ...]
    --proc models/forums-palace/yandex/forums-palace_yandex.obj
    --roof-tex work/forums-palace/roof/roof_sat.png
    [--ground Z] [--tris-per-piece N] [--tex 4096] [--renders DIR]

Look-alike colonnade facades fold together when Object Capture sees the whole capture
at once, so each facade is reconstructed separately (photos grouped by GPS sector) and
registered into the shared ENU frame (georef.json matrix: OBJ coords -> x East, y North,
z Up, metres, origin = footprint centre 41.30954 N, 69.28258 E). Each piece keeps only
the faces in its own facade sector (split along the building diagonals), inside the
podium outline and below the cornice top. Nobody photographs the roof from the ground,
so the roof, rooftop plant and dome come from the procedural Yandex model (whose cornice
height is measured from these scans) and are textured by top-down projection of
rectified satellite imagery (work/<lm>/roof).
"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../.omp/skills/photogrammetry-model/scripts"))
import render_utils as ru  # noqa: E402

LAT0, LON0 = 41.30954, 69.28258
ROT = math.radians(-37.15)        # local +u (long axis, towards SE) from east, CCW positive
L, W = 113.4, 86.6                # cornice outline = OSM footprint (roof texture extent)
A, B = L / 2 - 2.8, W / 2 - 2.8   # wall half extents (sector split along these diagonals)
U_MAX, V_MAX = A + 7.0, B + 6.0   # podium + stairs outline kept from the scans
H_TOP = 35.0                      # cornice top (façade scans), as in forums-palace_yandex.py
ROOF_DECK = H_TOP - 1.5           # recessed roof behind the parapet band

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir, opts = argv[0], argv[1:]


def opt(name, default=None, cast=str):
    return cast(opts[opts.index(name) + 1]) if name in opts else default


pieces = [opts[i + 1:i + 4] for i, a in enumerate(opts) if a == "--piece"]
if not pieces or opt("--proc") is None or opt("--roof-tex") is None:
    sys.exit(__doc__)
render_dir = opt("--renders", os.path.join(out_dir, "renders"))
os.makedirs(out_dir, exist_ok=True); os.makedirs(render_dir, exist_ok=True)
c, s = math.cos(-ROT), math.sin(-ROT)


def to_uv(x, y):
    return c * x - s * y, s * x + c * y


def sector(u, v):
    k = int(np.argmax([u / A, -u / A, v / B, -v / B]))
    return ("SE", "NW", "NE", "SW")[k]


def joined_import(path, **axes):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path, **axes)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:
        o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    if len(new) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.data.transform(ob.matrix_world)   # the importer puts axis conversion on the object
    ob.matrix_world = Matrix.Identity(4)
    return ob


ru.reset_scene()
parts, zs = [], []
for side, obj_path, geo_path in pieces:
    geo = json.load(open(geo_path))
    ob = joined_import(obj_path, forward_axis="Y", up_axis="Z")  # raw file coordinates
    me = ob.data
    me.transform(Matrix(geo["matrix"]))
    if me.has_custom_normals:
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bm = bmesh.new(); bm.from_mesh(me)
    drop = []
    for f in bm.faces:
        p = f.calc_center_median(); u, v = to_uv(p.x, p.y)
        if abs(u) > U_MAX or abs(v) > V_MAX or sector(u, v) != side:
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context="FACES")
    bm.to_mesh(me); bm.free()
    for m in me.materials:
        m.name = f"facade_{side}"
    ob.name = f"facade_{side}"
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    zs.append(co.reshape(-1, 3)[:, 2])
    parts.append(ob)
    print(f"{side}: kept {len(me.polygons)} faces (dropped {len(drop)}); "
          f"scale {geo.get('scale', float('nan')):.3f}, cam rms {geo.get('cam_rms_m', float('nan')):.2f} m")

ground = opt("--ground", None, float)
if ground is None:
    ground = float(np.percentile(np.concatenate(zs), 0.5))
print(f"ground z = {ground:.2f}")
target = opt("--tris-per-piece", 0, int)
for ob in parts:
    ob.data.transform(Matrix.Translation((0, 0, -ground)))
    bm = bmesh.new(); bm.from_mesh(ob.data)
    drop = [f for f in bm.faces   # plaza below the podium; roof noise above the cornice
            if not -0.3 <= f.calc_center_median().z <= H_TOP + 0.5]
    bmesh.ops.delete(bm, geom=drop, context="FACES"); bm.to_mesh(ob.data); bm.free()
    ntri = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if target and ntri > target:
        mod = ob.modifiers.new("dec", "DECIMATE"); mod.ratio = target / ntri
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=mod.name)

# roof, rooftop plant and dome: procedural geometry above the cornice, satellite texture
roof = joined_import(opt("--proc"))   # Y-up OBJ, default axes -> x East, y North, z up
bm = bmesh.new(); bm.from_mesh(roof.data)
def scanned(f):   # walls and colonnade below the roof deck come from the façade scans
    return min(v.co.z for v in f.verts) < ROOF_DECK - 0.05


bmesh.ops.delete(bm, geom=[f for f in bm.faces if scanned(f)], context="FACES")
uvl = bm.loops.layers.uv.new("UVMap")
for f in bm.faces:
    for lp in f.loops:
        u, v = to_uv(lp.vert.co.x, lp.vert.co.y)
        lp[uvl].uv = ((u + L / 2) / L, (v + W / 2) / W)
bm.to_mesh(roof.data); bm.free()
mat = bpy.data.materials.new("roof_satellite"); mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 1.0
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(opt("--roof-tex"))
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
roof.data.materials.clear(); roof.data.materials.append(mat)
roof.name = "roof"

bpy.ops.object.select_all(action="DESELECT")
for ob in parts + [roof]:
    ob.select_set(True)
bpy.context.view_layer.objects.active = roof
bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = "forums-palace"
for p in ob.data.polygons:
    p.use_smooth = False
ntri = sum(len(p.vertices) - 2 for p in ob.data.polygons)
co = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
dims = [float(x) for x in co.max(0) - co.min(0)]
print(f"final tris={ntri} dims(E,N,Up)={dims}")

texres = opt("--tex", 4096, int)
for img in bpy.data.images:
    if img.size[0] > texres:
        img.scale(texres, texres * img.size[1] // img.size[0])
glb = os.path.join(out_dir, "forums-palace.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_image_format="JPEG",
                          export_jpeg_quality=88, export_yup=True, export_apply=True)
geos = [json.load(open(g)) for _, _, g in pieces]
# merge into the hand-maintained metadata (Yandex stats, heights, sources) instead of replacing it
meta_path = os.path.join(out_dir, "forums-palace.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else dict(name="forums-palace", lat=LAT0, lon=LON0)
meta.setdefault("versions", {})["master"] = "forums-palace.glb"
meta.update(triangles_master=ntri,
            dimensions_master_m=dict(east_west=dims[0], north_south=dims[1], height=dims[2]),
            facades={side: dict(scale=g.get("scale"), camera_rms_m=g.get("cam_rms_m"),
                                cameras=g.get("n_cams")) for (side, _, _), g in zip(pieces, geos)},
            roof="procedural (OSM footprint, scanned cornice height) with rectified satellite "
                 "texture; not photographed")
json.dump(meta, open(meta_path, "w"), indent=1)
print(json.dumps(meta, indent=1))
ru.add_lights_world()
ru.render_turntable(ob, os.path.join(render_dir, "forums-palace"), textured=True, n=8)
