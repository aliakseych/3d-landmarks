"""Blender headless: textured master -> Yandex Maps 3D submission model.

blender -b -P blender_lowpoly.py -- <master_aligned.obj> <outDir> [options]
  --tris N           triangle budget after triangulation (default 14500; Yandex max 15000)
  --voxel V          voxel remesh size in metres (default 0.03): closes holes, merges
                     thin gaps, thickens nothing below ~V
  --smooth DEG       smooth-by-angle threshold (default 40)
  --dissolve DEG     limited-dissolve angle for flat n-gons (default 0.5; 0 = keep tris)
  --name NAME        output basename (default: model_yandex)
  --renders DIR      QA render dir (default: <outDir>/renders; keep it under work/ so
                     the published model folder holds only deliverables)
Input: Z-up metres, origin at base centre, base on z=0 (blender_master.py output).
Output: NAME.glb / NAME.obj / NAME.fbx (no materials, no UVs, no textures),
DIR/NAME_*.png (grey, backface culling ON so holes would show).
"""
import bpy, bmesh, math, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "../../photogrammetry-model/scripts"))
import render_utils as ru  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, out_dir = argv[:2]
opts = argv[2:]


def opt(name, default, cast=float):
    return cast(opts[opts.index(name) + 1]) if name in opts else default


budget = opt("--tris", 14500, int)
voxel = opt("--voxel", 0.03)
smooth = opt("--smooth", 40.0)
dissolve = opt("--dissolve", 0.5)
name = opt("--name", "model_yandex", str)
render_dir = opt("--renders", os.path.join(out_dir, "renders"), str)
os.makedirs(render_dir, exist_ok=True)


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def apply(ob, mod):
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


ru.reset_scene()
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
me = ob.data
# monochrome: no materials, UVs or colour attributes
me.materials.clear()
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
for a in [a.name for a in me.color_attributes]:
    me.color_attributes.remove(me.color_attributes[a])
if me.has_custom_normals:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
print(f"input tris={tri_count(me)} dims={tuple(round(d, 2) for d in ob.dimensions)}")

# 1. watertight single shell: voxel remesh (also removes internal/double walls).
# No automatic thickening: normal-push inflation (tried 0.2/0.3 m) turns cape edges, ears and
# crown points into knobs; the remeshed legs/arm already read at zoom 17-20.
m = ob.modifiers.new("remesh", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel; m.adaptivity = 0
apply(ob, m)

# 2. flat base exactly on z=0 (voxels round the bottom edge; no terrain height)
bm = bmesh.new(); bm.from_mesh(me)
cut = voxel * 0.75
res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, cut),
                             plane_no=(0, 0, 1), clear_inner=True)
edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
bmesh.ops.holes_fill(bm, edges=edges, sides=0)
for v in bm.verts:  # snap the cut rim/cap onto z=0
    if abs(v.co.z - cut) < 1e-5:
        v.co.z = 0.0
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
bm.to_mesh(me); bm.free()

# 3. decimate to budget (quadric collapse keeps silhouette; iterate to land under budget)
for _ in range(4):
    t = tri_count(me)
    if t <= budget:
        break
    m = ob.modifiers.new("dec", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = budget * 0.98 / t
    m.use_collapse_triangulate = True
    apply(ob, m)

bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
# drop tiny loose islands left by remesh/decimate
islands, seen = [], set()
bm.verts.ensure_lookup_table()
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        a = stack.pop(); comp.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen:
                seen.add(b.index); stack.append(b)
    islands.append(comp)
islands.sort(key=len, reverse=True)
print(f"islands after remesh/decimate: {[len(c) for c in islands[:8]]}")
for comp in islands[1:]:
    if len(comp) < 50:
        bmesh.ops.delete(bm, geom=comp, context="VERTS")
for v in bm.verts:  # decimation drifts base verts by <1 mm below the ground plane
    if v.co.z < 0:
        v.co.z = 0.0
# 4. n-gons on truly flat areas (base, pedestal faces); Yandex prefers n-gons
if dissolve > 0:
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve), verts=bm.verts[:], edges=bm.edges[:],
                             delimit=set())
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])  # consistent, outward
bm.to_mesh(me); bm.free()

# 5. smooth shading on rounded surfaces, hard edges above the angle
for p in me.polygons:
    p.use_smooth = True
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth), keep_sharp_edges=True)
me.update()

tris = tri_count(me)
ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
print(f"final faces={len(me.polygons)} tris(triangulated)={tris} ngons={ngons} "
      f"dims={tuple(round(d, 2) for d in ob.dimensions)} zmin={min(v.co.z for v in me.vertices):.4f}")
assert tris <= 15000, f"over Yandex budget: {tris}"

base = os.path.join(out_dir, name)
ob.name = me.name = name
bpy.ops.export_scene.gltf(filepath=base + ".glb", export_format="GLB", export_materials="NONE",
                          export_normals=True, export_yup=True, export_apply=True)
bpy.ops.wm.obj_export(filepath=base + ".obj", export_materials=False, export_uv=False, export_normals=True,
                      export_smooth_groups=True, forward_axis="NEGATIVE_Z", up_axis="Y")
bpy.ops.export_scene.fbx(filepath=base + ".fbx", use_selection=False, object_types={"MESH"},
                         mesh_smooth_type="FACE", use_mesh_modifiers=True, axis_forward="-Z", axis_up="Y",
                         apply_unit_scale=True, path_mode="STRIP", embed_textures=False)

ru.add_lights_world()
ru.render_turntable(ob, os.path.join(render_dir, name), textured=False, n=8, culling=True)
print("done", base)
