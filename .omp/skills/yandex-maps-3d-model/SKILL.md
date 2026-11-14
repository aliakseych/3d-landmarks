---
name: yandex-maps-3d-model
description: Use for simplifying a textured photogrammetry master into a Yandex Maps 3D submission (≤15k tris, untextured, closed, flat base, smooth shading; GLB/OBJ/FBX) and validating it against https://yandex.ru/project/maps/3d/tech.
---

# Master → Yandex Maps 3D model

Input: `work/<lm>/master/<lm>_aligned.obj` from skill `photogrammetry-model`. It is Z-up, in metres, with the origin at the base centre and the base on z=0.
Output: `models/<lm>/yandex/<lm>_yandex.{glb,obj,fbx}` plus one `preview.jpg` contact sheet. QA renders stay in `work/<lm>/yandex_renders/` (not published).

## Requirements (yandex.ru/project/maps/3d/tech)
- [ ] Only buildings and monuments are accepted, not bridges, billboards or lamps.
- [ ] The object only. No plaza, platform, terrain or trees. The base is flat; the terrain itself does not need to be modelled.
- [ ] **At most 15,000 triangles.** N-gons on flat areas are welcome.
- [ ] Recognisable at map zoom 17–20. Footprint, dimensions, silhouette and proportions match reality; small details may be simplified.
- [ ] Sculptures are simplified but must stay recognisable. An angular or inconsistent sculpture is worse than none.
- [ ] Thin, important elements are thickened slightly. Do not overdo it: an over-thickened model looks like a toy.
- [ ] Text is never geometry.
- [ ] Normals face outward. No double-sided walls and no double geometry.
- [ ] Closed from every side, **including the bottom**. The engine culls backfaces, and the camera will later go almost horizontal.
- [ ] Smooth shading on rounded parts, using the minimum geometry needed.
- [ ] No textures, lightmaps or material colours. Geometry only.
- [ ] Any polygon format works: FBX, OBJ or GLB.
- [ ] Legal: https://yandex.ru/legal/maps_mobile_agreement/. Photos must be your own. Submission rights are the user's call.

## Steps
Y = `.omp/skills/yandex-maps-3d-model/scripts`

1. **Simplify.**
   ```
   blender -b -P $Y/blender_lowpoly.py -- work/<lm>/master/<lm>_aligned.obj models/<lm>/yandex --name <lm>_yandex --renders work/<lm>/yandex_renders
   ```
   The script runs these steps:
   1. Strip materials, UVs and colours.
   2. Voxel remesh (`--voxel 0.03`). This gives one watertight shell and removes inner and double walls.
   3. Bisect at 0.75·voxel, cap the cut, and snap the cap to z=0.
   4. Iterative quadric decimate to `--tris 14500`.
   5. Weld and clamp z<0.
   6. `yandex_export.finish`: limited dissolve (`--dissolve 0.5`°) merges coplanar faces, then beauty triangulation. Exporters triangulate n-gons themselves, and keyhole n-gons (faces wrapped around a hole) came out as coincident up/down slivers that failed single shell; the triangle count is the same either way. It also drops islands smaller than 50 verts, recalculates normals and smooths by angle (`--smooth 40`°).
   7. `yandex_export.export`: GLB, OBJ and FBX, then a grey turntable render with backface culling on.

   The script fails if the triangle count is over 15,000.
2. **Validate.** Run `python3 $Y/validate.py models/<lm>/yandex/<lm>_yandex.glb` and the same for `.obj`. It checks:
   - no images, materials or UVs;
   - triangle count;
   - watertight;
   - consistent winding;
   - positive volume (outward normals);
   - single shell;
   - flat base at height 0.

   Any FAIL means the model is not ready. Also run `gltf-validator`; it should report 0 errors and 0 warnings.
3. **Visual QA.**
   - Build a contact sheet from `work/<lm>/yandex_renders/<lm>_yandex_az*_el+12.png` plus top and bottom views (crop 150,0,750,700 → 360×420, 5×2 grid, JPEG q85) and save it as `models/<lm>/yandex/preview.jpg`.
   - The horse/figure silhouette must read, and limbs must not be broken or webbed.
   - The bottom must be one flat cap.
   - Compare against the master renders taken from the same cameras: silhouette IoU per view should be above 0.95. Use a mask with `abs(img - bg) > 30`.
4. **Reimport check.** Import the FBX and OBJ back into Blender. Expect the same triangle count, metric dimensions, 0 materials, 0 UV layers and smooth faces.

## Buildings: procedural route
Ground photos of a large building miss the roof, and Object Capture often registers only some façades, so voxel-remeshing a scan gives a poor Yandex model. Model the building from data instead, one reproducible script per landmark in `scripts/landmarks/<lm>_yandex.py` (see `forums-palace_yandex.py`):
- **Footprint and heights** from OSM (`building`/`building:part` ways, `height`, `min_height`), converted to local metres around the footprint centre. That centre becomes the model origin and the `lat/lon` in the README/JSON.
- **Roof** (dome, plant boxes, recesses) from satellite imagery. **Façade rhythm** (columns, bays, cornice, podium, stairs) from photos.
- Build closed operand meshes, then run three EXACT boolean stages with collection operands: union of the body, difference of the cutters (windows, recesses), union of the roof items. Every operand must overlap its neighbour by ≥0.1 m with no coplanar or touching faces.
- Finish with `yandex_export.finish/report/export` (shared with `blender_lowpoly.py`), then follow Validate and Visual QA above. For visual QA, compare the renders against Commons photos and the satellite view instead of a master.
- `blender -b -P scripts/landmarks/<lm>_yandex.py -- models/<lm>/yandex --renders work/<lm>/yandex_renders`

## Tuning
| Knob | Effect |
|---|---|
| `--voxel` | 0.03 m keeps limb gaps for a ~9 m statue. Larger values fuse legs and webbing; smaller values cost decimation quality. Use roughly 1/300 of the height. |
| `--tris` | Keep a ~500-triangle margin under 15k; dissolve and FBX triangulation can differ slightly. |
| `--smooth` | 40° keeps the pedestal edges crisp and rounds the bronze. |
| `--dissolve` | Higher values make bigger flat n-gons but can flatten gentle curvature. |

**Thickening.** Automatic normal-push thickening (inward ray thickness, push by half the deficit, then re-remesh) was tried at 0.2 m and 0.3 m on amir-temur. Cape edges, ears and crown points turned into knobs, so it is not used. If a landmark has genuinely sub-voxel parts (spires, crosses), thicken them by hand in Blender on the master before running this step.

## Reference result (amir-temur)
- 14,182 triangles, 64 n-gons, extents 8.03 × 4.82 × 9.19 m.
- Watertight single shell, volume 64.3 m³.
- Silhouette IoU against the master is 0.965–0.979 over 12 views.

## Reference result (forums-palace, procedural)
- 7,302 triangles, extents 146.05 × 140.87 × 51.2 m, about 6 s of build time.
- Watertight single shell, volume 371,755 m³, flat base. gltf-validator reports 0 errors and 0 warnings.
