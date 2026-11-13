"""Shared Blender (Workbench) rendering helpers for visual QA. Imported by the
photogrammetry-model and yandex-maps-3d-model Blender scripts."""
import bpy, math, os
from mathutils import Matrix, Vector


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_lights_world():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.82, 0.86, 0.9)


def _shading(textured, flat=False, culling=True, color=(0.62, 0.62, 0.62)):
    sh = bpy.context.scene.display.shading
    sh.light = "FLAT" if flat else "STUDIO"
    sh.color_type = "TEXTURE" if textured else "SINGLE"
    sh.single_color = color
    sh.show_backface_culling = culling  # holes/inverted normals show as see-through
    sh.show_cavity = not textured
    if not textured:
        sh.cavity_type = "WORLD"
    bpy.context.scene.display.render_aa = "16"


def _camera(name="cam"):
    sc = bpy.context.scene
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def render_turntable(ob, prefix, textured=True, n=8, elevs=(12, 40), res=900, culling=True,
                     extra_views=("top", "bottom")):
    """Renders n azimuths x elevs plus top/bottom. Azimuth 0 = camera south of
    object looking north (ENU +Y = north). Returns list of paths."""
    sc = bpy.context.scene
    _shading(textured, culling=culling)
    sc.render.resolution_x = sc.render.resolution_y = res
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    ctr = sum(bb, Vector()) / 8
    rad = max((c - ctr).length for c in bb)
    cam = _camera()
    cam.data.lens, cam.data.sensor_width = 50, 36
    cam.data.clip_end = rad * 20
    d = rad / math.sin(math.atan(18 / 50)) * 1.02
    views = [(a, e) for e in elevs for a in range(0, 360, 360 // n)]
    views += [(0, 89.9)] if "top" in extra_views else []
    views += [(0, -89.9)] if "bottom" in extra_views else []
    out = []
    for az, el in views:
        a, e = math.radians(az), math.radians(el)
        pos = ctr + Vector((math.sin(a) * math.cos(e) * -1, -math.cos(a) * math.cos(e), math.sin(e))) * d
        cam.location = pos
        cam.rotation_euler = (ctr - pos).to_track_quat("-Z", "Y").to_euler()
        p = f"{prefix}_az{az:03d}_el{int(el):+03d}.png"
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    return out


def render_photo_overlays(ob, geo, shift, photos_dir, stems, out_dir, frame=None, res_long=1200):
    """Render the model from each photo's reconstructed camera (georef.json
    'cameras': c, R in ENU, f35) so it can be composited over the photo.
    frame: 'display' (portrait, pose in displayed orientation) or 'raw'
    (landscape sensor frame; rendered then rotated by compare.py)."""
    sc = bpy.context.scene
    _shading(True, flat=True, culling=True)
    sc.render.film_transparent = True
    frame = frame or geo.get("pose_frame", "raw")
    cam = _camera("photo_cam")
    S = shift.to_3x3().normalized()  # pure rotation part (similarity -> rotation)
    for stem in stems:
        c = geo["cameras"].get(stem + ".HEIC")
        if not c:
            continue
        Rw = S @ Matrix(c["R"])
        pos = shift @ Vector(c["c_model"])
        m = Rw.to_4x4(); m.translation = pos
        cam.matrix_world = m
        f35 = c.get("f35") or 29
        cam.data.sensor_fit = "AUTO"
        cam.data.sensor_width = 43.27 * 0.8  # long side of a 4:3 sensor with a 35mm-equivalent diagonal
        cam.data.lens = f35
        cam.data.clip_start, cam.data.clip_end = 0.05, 500
        w, h = (res_long, res_long * 3 // 4) if frame == "raw" else (res_long * 3 // 4, res_long)
        sc.render.resolution_x, sc.render.resolution_y = w, h
        sc.render.filepath = os.path.join(out_dir, f"cam_{stem}_{frame}.png")
        bpy.ops.render.render(write_still=True)
    sc.render.film_transparent = False
