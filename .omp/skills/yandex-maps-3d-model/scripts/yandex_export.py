"""Shared Yandex Maps submission helpers (Blender): finishing pass, triangle count,
GLB/OBJ/FBX export without materials, UVs or textures. Imported by blender_lowpoly.py
(scanned objects) and scripts/landmarks/*_yandex.py (procedural buildings)."""
import bpy, bmesh, math

YANDEX_MAX_TRIS = 15000


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def drop_islands(bm, min_verts=50):
    """Deletes connected components (except the largest) with fewer than min_verts vertices."""
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
    print(f"islands: {[len(c) for c in islands[:8]]}")
    for comp in islands[1:]:
        if len(comp) < min_verts:
            bmesh.ops.delete(bm, geom=comp, context="VERTS")


def finish(ob, smooth_deg=40.0, dissolve_deg=0.5, min_island_verts=50):
    """Limited dissolve, beauty triangulation, small-island removal, outward normals,
    smooth by angle. Strips UV/colour layers and materials."""
    me = ob.data
    for attr in [a.name for a in me.color_attributes]:
        me.color_attributes.remove(me.color_attributes[attr])
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.materials.clear()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    if dissolve_deg > 0:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:],
                                 edges=bm.edges[:], delimit=set())
    # Boolean/dissolve n-gons can wrap around holes (keyholes); the exporters' own triangulation
    # of those emits coincident up/down slivers outside the closed hull (palace drum/roof seam).
    # Beauty triangulation here avoids them; the exported triangle count is unchanged.
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
    drop_islands(bm, min_island_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_deg), keep_sharp_edges=True)
    me.update()


def report(ob, max_tris=YANDEX_MAX_TRIS):
    me = ob.data
    tris = tri_count(me)
    ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
    print(f"final faces={len(me.polygons)} tris(triangulated)={tris} ngons={ngons} "
          f"dims={tuple(round(d, 2) for d in ob.dimensions)} zmin={min(v.co.z for v in me.vertices):.4f}")
    assert tris <= max_tris, f"over Yandex budget: {tris} > {max_tris}"
    return tris


def export(ob, base):
    """Writes base.glb/.obj/.fbx. Scene must contain only this mesh object."""
    ob.name = ob.data.name = base.rsplit("/", 1)[-1]
    bpy.ops.export_scene.gltf(filepath=base + ".glb", export_format="GLB", export_materials="NONE",
                              export_normals=True, export_yup=True, export_apply=True)
    bpy.ops.wm.obj_export(filepath=base + ".obj", export_materials=False, export_uv=False,
                          export_normals=True, export_smooth_groups=True,
                          forward_axis="NEGATIVE_Z", up_axis="Y")
    bpy.ops.export_scene.fbx(filepath=base + ".fbx", use_selection=False, object_types={"MESH"},
                             mesh_smooth_type="FACE", use_mesh_modifiers=True, axis_forward="-Z",
                             axis_up="Y", apply_unit_scale=True, path_mode="STRIP", embed_textures=False)
