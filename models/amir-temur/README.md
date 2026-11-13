# Amir Temur monument, Tashkent

Equestrian statue on Amir Temur Square. This model was reconstructed from 32 of the author's own iPhone photos using Apple Object Capture and Blender. The pipeline is in `.omp/skills/photogrammetry-model` and `.omp/skills/yandex-maps-3d-model`.

| File | Use | Triangles | Notes |
|---|---|---|---|
| `amir-temur.glb` | Sharing and app viewing (textured master) | 137,478 | 4096 px JPEG baked texture, 5.0 MB |
| `yandex/amir-temur_yandex.glb` | Yandex Maps 3D submission | 14,182 | No materials or UVs; watertight; smooth shaded; 64 flat n-gons |
| `yandex/amir-temur_yandex.obj` | Same model as OBJ | 14,182 | Y up |
| `yandex/amir-temur_yandex.fbx` | Same model as FBX | 14,182 | Blender FBX export; Y up; unit scale 1 = 1 m |
| `yandex/preview.jpg` | Grey turntable of the Yandex model (8 views + top + bottom) | — | QA contact sheet |
| `amir-temur.json` | Metadata | — | lat/lon, dimensions, axes, georeference quality |

- **Location:** the origin is the base centre, at lat `41.3111744`, lon `69.2797594` (WGS84).
- **Axes:** metres. In glTF, +Y is up, +X is east and −Z is north. The OBJ and FBX files use the same Y-up convention. The base is flat at height 0.
- **Dimensions** (E-W × N-S × height):
  - master: 8.14 × 4.88 × 9.23 m;
  - Yandex: 8.03 × 4.82 × 9.19 m. It is about 4 cm smaller per side because of the voxel remesh.
- **What it covers:** the horse, the rider and the granite pedestal down to where it meets the lawn, including the small bottom flare. The lawn, paving, flower beds and trees are excluded, as Yandex requires.

## Accuracy and limitations
- **Scale** comes from photo GPS: 1.2 % fit error, 1.05 m RMS. Expect the absolute size to be off by about 1–5 %.
- **Heading** comes from GPS. The compass agrees within 1.7°.
- **Unseen surfaces.** Some tops (shoulders, crown, upper horse back) were not visible from the ground. Those holes were closed geometrically and tinted to bronze, so they are plausible rather than measured.
- **Legal.** Before submitting, check the Yandex terms: https://yandex.ru/legal/maps_mobile_agreement/
