#!/usr/bin/env python3
"""Georeference an Object Capture reconstruction from photo GPS + compass.

usage: georef.py <poses.json> <imagesDir> <out.json> [--up y|pca]

Model frame = OBJ written by objcap (RealityKit: Y up, metres-ish, arbitrary
heading/scale). Output: 4x4 matrix M (row-major) mapping model coords to a local
ENU frame (x=East, y=North, z=Up, metres) centred on the weighted GPS centroid,
plus that centroid's lat/lon. Scale/heading come from a weighted 2-D similarity
fit of camera centres to GPS positions; compass (GPSImgDirection) gives an
independent heading check. Scale is only as good as GPS (~3-15 m per shot):
check `scale_rel_err` and sanity-check real dimensions.
"""
import json, math, subprocess, sys
import numpy as np

R_EARTH = 6378137.0


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def rot_a_to_b(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(np.dot(a, b))
    if c < -0.999999:
        return np.diag([1.0, -1.0, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def circmean(a):
    return math.atan2(np.mean(np.sin(a)), np.mean(np.cos(a)))


def main():
    args = sys.argv[1:]
    up_mode = "y"
    if "--up" in args:
        i = args.index("--up"); up_mode = args[i + 1]; del args[i:i + 2]
    poses_path, img_dir, out_path = args
    poses = json.load(open(poses_path))
    exif = json.loads(subprocess.check_output([
        "exiftool", "-n", "-json", "-GPSLatitude", "-GPSLongitude", "-GPSAltitude",
        "-GPSHPositioningError", "-GPSImgDirection", "-FocalLengthIn35mmFormat", img_dir]))
    ex = {e["SourceFile"].split("/")[-1]: e for e in exif}

    C, F, G, W, H, Rs, names = [], [], [], [], [], [], []
    for p in poses:
        e = ex.get(p["file"])
        if not e or "GPSLatitude" not in e:
            continue
        R = quat_to_mat(p["q"])
        C.append(p["t"]); F.append(-R[:, 2]); Rs.append(R); names.append(p["file"])
        G.append((e["GPSLatitude"], e["GPSLongitude"]))
        W.append(1.0 / max(e.get("GPSHPositioningError", 10.0), 2.0) ** 2)
        H.append(e.get("GPSImgDirection", np.nan))
    C, F, G, W, H = map(np.array, (C, F, G, W, H))
    n = len(C)
    if n < 4:
        sys.exit(f"only {n} geotagged registered cameras")

    # Up vector: RealityKit output is gravity-aligned (+Y) when photos carry
    # gravity metadata; PCA normal of the camera ring is the cross-check.
    Cc = C - C.mean(0)
    normal = np.linalg.svd(Cc)[2][2]
    if normal[1] < 0:
        normal = -normal
    up = np.array([0.0, 1.0, 0.0]) if up_mode == "y" else normal
    tilt = math.degrees(math.acos(min(1, abs(normal[1]))))
    R0 = rot_a_to_b(up, np.array([0.0, 0.0, 1.0]))
    Ch = (R0 @ C.T).T
    Fh = (R0 @ F.T).T
    p = Ch[:, :2]

    lat0 = float(np.average(G[:, 0], weights=W)); lon0 = float(np.average(G[:, 1], weights=W))
    g = np.c_[np.radians(G[:, 1] - lon0) * R_EARTH * math.cos(math.radians(lat0)),
              np.radians(G[:, 0] - lat0) * R_EARTH]

    # weighted 2-D Umeyama similarity g ~ s*Rot(th)*p + t
    w = W / W.sum()
    mp, mg = w @ p, w @ g
    pc, gc = p - mp, g - mg
    S = (gc * w[:, None]).T @ pc
    U, D, Vt = np.linalg.svd(S)
    Rz = U @ np.diag([1, np.sign(np.linalg.det(U @ Vt))]) @ Vt
    var_p = (w * (pc ** 2).sum(1)).sum()
    s = float(np.trace(np.diag(D) @ np.diag([1, np.sign(np.linalg.det(U @ Vt))])) / var_p)
    th_gps = math.atan2(Rz[1, 0], Rz[0, 0])
    resid = g - (s * (Rz @ pc.T).T + mg)
    rms = float(np.sqrt((w * (resid ** 2).sum(1)).sum()))
    # scale uncertainty ~ position noise / spread of the camera ring
    spread = float(np.sqrt(var_p)) * s
    scale_rel_err = rms / spread / math.sqrt(max(n - 2, 1))

    # compass heading check: heading = atan2(E, N) clockwise from north
    ok = ~np.isnan(H)
    hm = np.arctan2(Fh[ok, 0], Fh[ok, 1])
    th_cmp = circmean(hm - np.radians(H[ok]))  # CCW rotation model->ENU
    dcmp = np.degrees((hm - th_cmp - np.radians(H[ok]) + np.pi) % (2 * np.pi) - np.pi)

    # final: GPS rotation unless it disagrees strongly with compass
    diff = math.degrees((th_gps - th_cmp + math.pi) % (2 * math.pi) - math.pi)
    th = th_gps if abs(diff) < 20 else th_cmp
    c, si = math.cos(th), math.sin(th)
    Rth = np.array([[c, -si, 0], [si, c, 0], [0, 0, 1]])
    L = s * Rth @ R0
    t2 = mg - s * (np.array([[c, -si], [si, c]]) @ mp)
    # z: put mean camera height at +1.5 m (eye/hand height above ground level)
    tz = 1.5 - s * float(Ch[:, 2].mean())
    M = np.eye(4); M[:3, :3] = L; M[:3, 3] = [t2[0], t2[1], tz]

    out = dict(matrix=M.tolist(), lat0=lat0, lon0=lon0, scale=s, scale_rel_err=scale_rel_err,
               heading_gps_deg=math.degrees(th_gps), heading_compass_deg=math.degrees(th_cmp),
               heading_used_deg=math.degrees(th), gps_vs_compass_deg=diff,
               compass_residual_std_deg=float(np.std(dcmp)), gps_rms_m=rms,
               cam_ring_radius_m=spread, up_mode=up_mode, ring_tilt_vs_y_deg=tilt, n=n,
               cameras={nm: dict(c=(M[:3, :3] @ c_ + M[:3, 3]).tolist(), c_model=c_.tolist(), R=r_.tolist(),
                                 f35=ex[nm].get("FocalLengthIn35mmFormat"), compass=ex[nm].get("GPSImgDirection"))
                        for nm, c_, r_ in zip(names, C, Rs)})
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("matrix", "cameras")}, indent=1))

if __name__ == "__main__":
    main()
