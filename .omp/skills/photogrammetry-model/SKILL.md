---
name: photogrammetry-model
description: Use for turning a folder of phone photos of a landmark/monument into a georeferenced, medium-res textured 3D master (GLB, ~100-250k tris, 4K texture) with Apple Object Capture + Blender headless; first stage before yandex-maps-3d-model.
---

# Photos → textured master model

Output is the **master**: a cleaned, textured, georeferenced GLB detailed enough to share in
an app (~100–250k triangles, 4K JPEG texture). The Yandex submission is derived from it
(skill `yandex-maps-3d-model`).

## Layout
| Path | Role |
|---|---|
| `temp-captures/<landmark>/` | raw photos (HEIC + Live Photo MOV, often one folder per shot). **Read-only, local only** (gitignored: originals carry GPS EXIF and are ~0.5 GB per landmark). |
| `work/<landmark>/` | intermediates: `images/` (hard links), `photos/` (1200px JPEGs), `oc1/`, `georef.json`, `master/` |
| `models/<landmark>/` | deliverables: `<landmark>.glb`, `<landmark>.json`, `yandex/` |

## Tools
- macOS on Apple Silicon (Object Capture), Blender ≥ 4.2 (tested on 5.3: `blender` on PATH), exiftool.
- python3 with numpy, PIL, trimesh, scipy. Blender's own Python has no PIL, so do image compositing outside Blender.
- `npm -g gltf-validator` is a library, not a CLI. Run it as `NODE_PATH=$(npm root -g) node -e "require('gltf-validator').validateBytes(...)"`.
- COLMAP (brew) is the fallback when Object Capture fails to register enough shots.

## Capture checklist
- 30–60 photos all around the object, from 2–3 distances. Overlap should be at least 60%.
- Add a few zoomed shots of the figure and the top parts. The tops of a statue are never seen from the ground, so they get filled and tinted later.
- Keep GPS and compass on. `georef.py` uses EXIF GPS and `GPSImgDirection` for scale, heading and lat/lon.
- Overcast light is best. Bright sky behind a dark bronze figure gets fused into "sky membranes", which step 4 removes.

## Steps
S = `.omp/skills/photogrammetry-model/scripts`

1. **Stage photos.** Never touch the raw folder. List blurred shots, crowd shots and shots with no overlap as excludes.
   ```
   $S/prep_photos.sh temp-captures/<landmark> work/<landmark> IMG_1151 IMG_1154 ...
   ```
2. **Reconstruct.** Build the CLI once: `swiftc -O -parse-as-library $S/objcap.swift -o $S/objcap`. Then run:
   ```
   $S/objcap work/<lm>/images work/<lm>/oc1 custom --polys 250000 --tex 8192 > work/<lm>/oc1.log
   ```
   - Takes about 10–20 min for 32 HEICs on an M4.
   - Writes `oc1/model/*.obj` (+ 8K `_tex0.png`, `_norm0.png`), `poses.json` and `bounds.json`.
   - Check the log: all shots should be registered.
3. **Georeference.**
   ```
   python3 $S/georef.py work/<lm>/oc1/poses.json work/<lm>/images work/<lm>/georef.json
   ```
   Check the output:
   - `gps_rms_m` should be a few metres or less.
   - `scale_rel_err` should be below 0.03.
   - `gps_vs_compass_deg` should be below 10°.
   - `ring_tilt_vs_y_deg` should be close to 0. Model up is +Y for Object Capture. Use `--up pca` only if the shots were not level.
4. **Find crop parameters.**
   ```
   blender -b -P $S/blender_master.py -- <obj> georef.json analyze --analyze --photos photos
   ```
   This prints a radial z-profile around the auto-detected axis and renders raw aligned views. Read them to choose:
   - `--center X,Y`: the statue axis, in ENU metres.
   - `--radius R`: just outside the pedestal. It drops the plaza, steps and trees.
   - `--base-z Z`: where the pedestal meets the ground or platform.
5. **Build the master.** amir-temur values are shown; run from `work/<lm>`.
   ```
   blender -b -P ../../$S/blender_master.py -- oc1/model/<mesh>.obj georef.json master \
     --center -2.385,-3.838 --radius 4.5 --base-z 1.4 --sky 0.8 --sky-above 4 --sky-tint 0.5 \
     --fill-holes 400 --tex 4096 --name <lm> --photos photos
   ```
   The script then:
   - welds Object Capture slits;
   - deletes sky membranes (faces whose texture luminance is above `--sky`, above `--sky-above`);
   - keeps the main island;
   - caps the flat base with one n-gon;
   - closes the remaining holes (holes_fill, then a centroid-fan fallback for loops holes_fill rejects);
   - retints bright texels on the statue and the fill faces;
   - exports `master/<lm>.glb` (Y-up), `<lm>_aligned.obj` (Z-up, input for the Yandex step) and `<lm>.json` (lat/lon, dims, axes).
6. **QA. Do not ship without looking.**
   - Turntable contact sheet:
     - files: `renders/<lm>_az*_el+12.png` plus `_az000_el+89/-89`;
     - crop each to (150, 0, 750, 700) and use a 5×2 PIL grid.
     - Look for: no sky sheets or floating blobs, plaza removed, top of the pedestal visible, bottom capped.
   - Photo overlays: `python3 $S/compare.py work/<lm>/master/renders work/<lm>/photos /tmp/cmp.jpg`.
     - Each row is photo | render | red outline over the photo.
     - The outline must hug the photo silhouette: raised hand, head and tail.
   - Validator: `gltf-validator` should report 0 errors, and `totalTriangleCount` should be in the 100–250k range.
7. **Deliver.** Copy `master/<lm>.glb` and `<lm>.json` to `models/<lm>/`. Then delete `try*`, `analyze` and other scratch dirs; free disk is usually the limit.

## Tuning notes
| Knob | Effect | amir-temur |
|---|---|---|
| `--sky` | Lower values remove more. At 0.6 the raised hand and parts of the torso disappeared; 0.72 was still too aggressive. | **0.8** |
| `--sky-above` | Protects bright stone below this height (light granite, plinth). | 4 m |
| `--sky-tint` | Recolours leftover sky-blue texels on tops no camera saw. Lower values recolour more. | 0.5 |
| `--fill-holes` | Maximum loop length closed. Large loops sit on unobserved tops (shoulders, crown). | 400 |
| `--base-z` | Includes about 0.15 m of plinth flare. Raise it if steps leak in. | 1.4 |
| `--tris` | Leave unset when Object Capture's 250k → ~137k after crop is already in range. | — |

## Pitfalls
- **Do not run `recalc_face_normals` on the open photogrammetry mesh.** It flipped the pedestal top. Object Capture winding is already outward; new faces copy their neighbour's winding.
- Object Capture leaves unwelded slits that look like holes. Weld first (`remove_doubles` 1e-5), otherwise holes_fill skips them.
- The master can keep a few non-manifold edges. The Yandex step re-shells via voxel remesh, so only the low-poly has to be watertight.
- `ob.dimensions` is stale after bmesh edits. Compute dimensions from vertex coordinates.
- Workbench renders are fast and need no GPU. Overlays use the `raw` pose frame, which is the one that matched the photos.
- The aligned OBJ copies the 8K texture (~45 MB). Keep it in `work/`, not in `models/`.
