"""Procedural Yandex Maps 3D model: Palace of International Forums "Uzbekistan"
(O'zbekiston Anjumanlar Saroyi, Tashkent).

blender -b -P scripts/landmarks/forums-palace_yandex.py -- <outDir> [--renders DIR]

Writes <outDir>/forums-palace_yandex.{glb,obj,fbx} (one closed monochrome shell, n-gons,
<= 15k triangles) and grey QA renders.

Sources: OpenStreetMap way 44351799 (footprint 113.4 x 86.6 m, long axis bearing 127 deg)
and way 235797552 (dome position); cornice top 35 m measured from the facade photo scans
(OSM's 40.2 m tag overstates it); dome top 48 m = official building height
(mustaqillik.uz); dome radius from satellite imagery (OSM 31.8 m is too large); photos.
Frame: origin = footprint centre (41.30954 N, 69.28258 E) on the ground, X east, Y north,
Z up, metres (glTF/OBJ/FBX exports are Y-up, -Z north). Local building axes: u = long
axis (towards SE), v = short axis (towards NE); the NW short facade faces Amir Temur square.
Omitted: the stork sculpture on the dome (would not read at map zoom), ornament reliefs,
surrounding plazas and terrain.
"""
import bpy, bmesh, math, os, sys
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "../../.omp/skills")
sys.path.insert(0, os.path.join(SKILLS, "yandex-maps-3d-model/scripts"))
sys.path.insert(0, os.path.join(SKILLS, "photogrammetry-model/scripts"))
import render_utils as ru  # noqa: E402
import yandex_export as yx  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir = argv[0]
render_dir = argv[argv.index("--renders") + 1] if "--renders" in argv else os.path.join(out_dir, "renders")
os.makedirs(out_dir, exist_ok=True); os.makedirs(render_dir, exist_ok=True)
NAME = "forums-palace_yandex"

# --- dimensions (metres) -----------------------------------------------------------------
L, W = 113.4, 86.6           # cornice outline = OSM footprint
ROT = -37.15                 # local +u from east, degrees (counter-clockwise positive)
CORNICE_OUT = 2.8            # top cornice projection beyond the wall plane
A, B = L / 2 - CORNICE_OUT, W / 2 - CORNICE_OUT   # wall half extents
H_TOP = 35.0                 # cornice/parapet top (facade scans: SE 35.2, NW 34.1)
ENT_H = 8.5                  # entablature + cornice height
COL_TOP = H_TOP - ENT_H
POD_H, POD_OUT = 1.2, 4.0    # podium height, projection beyond the wall
STEPS, TREAD, STAIR_HW = 4, 0.45, 26.0   # stairs on the NW and SE facades
PYLON = 15.0                 # corner pylon width on each facade
COL_R, COL_OFF, COL_SEG = 1.0, 0.6, 16   # engaged round columns: radius, axis offset, sides
N_COLS = {"short": 8, "long": 12}
WIN_DEPTH, WIN_RISE = 1.2, 2.5           # recessed glazed bays with pointed-arch heads
ROOF_INSET, ROOF_DROP = 5.5, 1.5         # parapet band width (from cornice edge), roof drop
DOME_U, DOME_V, DOME_R, DOME_TOP = -8.87, 0.0, 29.0, 48.0
DOME_SEG, DOME_RINGS, RIB = 64, 10, 0.25  # 32 ribs = every other vertex pushed out by RIB
ROOF_BLOCKS = [  # (u0, u1, v0, v1, height) rooftop plant, from satellite imagery
    (-48, -22, 30, 37, 3.0), (-48, -24, -37, -30, 3.0), (14, 48, 24, 33, 2.5),
    (16, 48, -33, -23, 2.5), (28, 48, -20, 20, 2.0)]

coll_add = coll_cut = coll_roof = None


def mesh(name, verts, faces, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])  # boolean operands must face outward
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def box(u0, u1, v0, v1, z0, z1, coll=None):
    v = [(u0, v0, z0), (u1, v0, z0), (u1, v1, z0), (u0, v1, z0),
         (u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh("box", v, f, coll or coll_add)


def prism(ring, z0, z1, coll=None):
    """Vertical prism over a CCW (u, v) polygon."""
    n = len(ring)
    v = [(x, y, z0) for x, y in ring] + [(x, y, z1) for x, y in ring]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    f += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh("prism", v, f, coll or coll_add)


def circle(cu, cv, r, seg):
    return [(cu + r * math.cos(2 * math.pi * i / seg), cv + r * math.sin(2 * math.pi * i / seg))
            for i in range(seg)]


# facade frames: centre (u, v), tangent t (t x Z = n), outward normal n, half length, kind
FACADES = [((-A, 0), (0, -1), (-1, 0), B, "short"),  # NW, Amir Temur square
           ((A, 0), (0, 1), (1, 0), B, "short"),     # SE
           ((0, -B), (1, 0), (0, -1), A, "long"),    # SW
           ((0, B), (-1, 0), (0, 1), A, "long")]     # NE


def fpt(fr, s, n):
    (cu, cv), (tu, tv), (nu, nv) = fr[0], fr[1], fr[2]
    return cu + s * tu + n * nu, cv + s * tv + n * nv


def fbox(fr, s0, s1, n0, n1, z0, z1, coll=None):
    (u0, v0), (u1, v1) = fpt(fr, s0, n0), fpt(fr, s1, n1)
    return box(min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1), z0, z1, coll)


def arch_window(fr, s_c, width, z0, apex, depth):
    """Cutter: rectangle + two-centred pointed arch in the facade plane, extruded inward."""
    w, h = width / 2, WIN_RISE
    R = (w * w + h * h) / (2 * w)
    zs = apex - h
    prof = [(s_c - w, z0), (s_c + w, z0)]
    th_a = math.atan2(h, R - w)            # right arc (centre s_c + w - R) end angle at apex
    for k in range(5):                      # right side, bottom -> apex
        t = th_a * k / 4
        prof.append((s_c + w - R + R * math.cos(t), zs + R * math.sin(t)))
    for k in range(3, -1, -1):              # left side, apex -> bottom (mirror)
        t = th_a * k / 4
        prof.append((s_c - (w - R + R * math.cos(t)), zs + R * math.sin(t)))
    prof = [p for i, p in enumerate(prof) if i == 0 or (abs(p[0] - prof[i - 1][0]) + abs(p[1] - prof[i - 1][1])) > 1e-6]
    n = len(prof)
    verts = []
    for nn in (0.5, -depth):
        for s, z in prof:
            u, v = fpt(fr, s, nn)
            verts.append((u, v, z))
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mesh("win", verts, faces, coll_cut)


def dome():
    zb, zt = H_TOP + 0.6, DOME_TOP
    h = zt - zb
    Rs = (DOME_R ** 2 + h ** 2) / (2 * h)
    zc = zt - Rs
    phi_max = math.asin(DOME_R / Rs)
    rings = []
    # drum: from below the recessed roof up to zb
    rings.append((DOME_R, H_TOP - ROOF_DROP - 0.3, False))
    for k in range(DOME_RINGS, 0, -1):
        phi = phi_max * k / DOME_RINGS
        rings.append((Rs * math.sin(phi), zc + Rs * math.cos(phi), True))
    verts = []
    for r, z, ribbed in rings:
        for j in range(DOME_SEG):
            rr = r + (RIB * r / DOME_R if ribbed and j % 2 == 0 else 0.0)
            a = 2 * math.pi * j / DOME_SEG
            verts.append((DOME_U + rr * math.cos(a), DOME_V + rr * math.sin(a), z))
    nr, s = len(rings), DOME_SEG
    faces = [tuple(range(s - 1, -1, -1)), tuple(range((nr - 1) * s, nr * s))]
    for i in range(nr - 1):
        for j in range(s):
            faces.append((i * s + j, i * s + (j + 1) % s, (i + 1) * s + (j + 1) % s, (i + 1) * s + j))
    mesh("dome", verts, faces, coll_roof)
    # finial pedestal for the (omitted) sculpture
    prism(circle(DOME_U, DOME_V, 2.2, 16), zt - 0.6, zt + 1.2, coll_roof)


def build():
    global coll_add, coll_cut, coll_roof
    sc = bpy.context.scene
    coll_add, coll_cut, coll_roof = (bpy.data.collections.new(n) for n in ("add", "cut", "roof"))
    for c in (coll_add, coll_cut, coll_roof):
        sc.collection.children.link(c)
    # podium (closed base on z=0) and the wall block
    body = box(-A - POD_OUT, A + POD_OUT, -B - POD_OUT, B + POD_OUT, 0.0, POD_H, sc.collection)
    box(-A, A, -B, B, POD_H - 0.1, COL_TOP + 0.5)
    # stairs on the NW and SE facades
    rise = POD_H / STEPS
    for sgn in (-1, 1):
        for k in range(STEPS):
            out = A + POD_OUT + (STEPS - k) * TREAD
            u0, u1 = sorted((sgn * (A + POD_OUT - 0.2), sgn * out))
            box(u0, u1, -STAIR_HW, STAIR_HW, 0.0, rise * (k + 1))
    # entablature and cornice: stacked full boxes, overlapping 2 cm
    for z0, z1, out in ((COL_TOP, COL_TOP + 3.2, 2.0), (COL_TOP + 3.18, H_TOP - 1.4, 2.4),
                        (H_TOP - 1.42, H_TOP, CORNICE_OUT)):
        box(-A - out, A + out, -B - out, B + out, z0, z1)
    # recessed roof inside the parapet band; rooftop plant boxes
    ri = ROOF_INSET
    box(-L / 2 + ri, L / 2 - ri, -W / 2 + ri, W / 2 - ri, H_TOP - ROOF_DROP, H_TOP + 1.0, coll_cut)
    for u0, u1, v0, v1, hh in ROOF_BLOCKS:
        box(u0, u1, v0, v1, H_TOP - ROOF_DROP - 0.1, H_TOP - ROOF_DROP + hh, coll_roof)
    dome()
    # facades: corner pylons with a tall slit window and a shallow panel, columns and bays
    apex = COL_TOP - 0.8
    for fr in FACADES:
        half, kind = fr[3], fr[4]
        for sgn in (-1, 1):
            arch_window(fr, sgn * (half - 3.5), 3.0, POD_H + 0.15, apex, WIN_DEPTH)
            s0, s1 = sorted((sgn * (half - 6.5), sgn * (half - PYLON + 1.5)))
            fbox(fr, s0, s1, 0.5, -0.35, POD_H + 3.0, COL_TOP - 3.0, coll_cut)
        n_col = N_COLS[kind]
        c0, c1 = -half + PYLON + 1.2, half - PYLON - 1.2
        step = (c1 - c0) / (n_col - 1)
        cols = [c0 + i * step for i in range(n_col)]
        for s in cols:
            u, v = fpt(fr, s, COL_OFF)
            prism(circle(u, v, COL_R, COL_SEG), POD_H - 0.05, COL_TOP + 0.05)
            fbox(fr, s - 1.2, s + 1.2, -0.2, COL_OFF + 1.25, POD_H - 0.05, POD_H + 1.0)
            fbox(fr, s - 1.2, s + 1.2, -0.2, COL_OFF + 1.25, COL_TOP - 1.2, COL_TOP + 0.05)
        for a, b in zip(cols, cols[1:]):
            arch_window(fr, (a + b) / 2, step - 2.6, POD_H + 0.15, apex, WIN_DEPTH)
    # booleans (EXACT, overlapping operands only): union walls/columns, cut bays and the
    # roof recess, then union dome and rooftop plant onto the recessed roof
    bpy.context.view_layer.objects.active = body
    for op, coll in (("UNION", coll_add), ("DIFFERENCE", coll_cut), ("UNION", coll_roof)):
        m = body.modifiers.new(op, "BOOLEAN")
        m.operation, m.operand_type, m.collection, m.solver = op, "COLLECTION", coll, "EXACT"
        bpy.ops.object.modifier_apply(modifier=m.name)
    for coll in (coll_add, coll_cut, coll_roof):
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob)
        bpy.data.collections.remove(coll)
    # local (u, v) -> ENU
    body.data.transform(Matrix.Rotation(math.radians(ROT), 4, "Z"))
    for v in body.data.vertices:
        if v.co.z < 1e-4:
            v.co.z = 0.0
    return body


ru.reset_scene()
ob = build()
yx.finish(ob, smooth_deg=40.0, dissolve_deg=0.5)
yx.report(ob)
yx.export(ob, os.path.join(out_dir, NAME))
ru.add_lights_world()
ru.render_turntable(ob, os.path.join(render_dir, NAME), textured=False, n=8, culling=True)
print("done", NAME)
