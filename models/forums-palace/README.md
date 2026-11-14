# Palace of International Forums "Uzbekistan", Tashkent

Domed conference palace on Istiqbol Street, beside Amir Temur Square. This is a procedural Blender model (`scripts/landmarks/forums-palace_yandex.py`). Its footprint comes from OpenStreetMap and satellite imagery. Its heights come from photogrammetry scans of the author's 114 iPhone photos and the official building height.

**Textured master: pending.** The photos reconstruct only the SE and NW facades. The NE and SW facades were shot from about six spots 30–60 m away, with too little baseline. Apple Object Capture rejected them in every mode tried (unordered, sequential, normal sensitivity, extra overlap photos). The master needs a new capture walk along those two facades.

| File | Use | Triangles | Notes |
|---|---|---|---|
| `yandex/forums-palace_yandex.glb` | Yandex Maps 3D submission | 7,416 | No materials or UVs; one watertight shell; smooth shaded; fully triangulated |
| `yandex/forums-palace_yandex.obj` | Same model as OBJ | 7,416 | Y up |
| `yandex/forums-palace_yandex.fbx` | Same model as FBX | 7,416 | Blender FBX export; Y up; unit scale 1 = 1 m |
| `yandex/preview.jpg` | Grey turntable of the Yandex model (8 views + top + bottom) | — | QA contact sheet |
| `forums-palace.json` | Metadata | — | lat/lon, dimensions, axes, height sources |

- **Location:** the origin is the footprint centre at ground level, at lat `41.30954`, lon `69.28258` (WGS84).
- **Axes:** metres. In glTF, +Y is up, +X is east and −Z is north. The base is flat at height 0.
- **Dimensions** (E-W × N-S × height): 146.1 × 140.9 × 49.2 m bounding box. The building is a 113.4 × 86.6 m rectangle with its long axis at bearing 127°. It is wrapped by a podium with stairs on the NW and SE facades.
- **What it covers:** podium and stairs, colonnaded walls with engaged columns and recessed arched bays, entablature and cornice, parapet roof with rooftop plant blocks, and the ribbed dome on its drum.

## Accuracy and limitations
- **Scale:**
  - The footprint is OSM way 44351799 (the cornice outline), checked against satellite imagery.
  - The cornice top is 35 m, from scans of the SE (35.2 m) and NW (34.1 m) facades. OSM's 40.2 m tag overstates it.
  - The dome top is 48 m, which is the official building height (mustaqillik.uz). A 1.2 m finial pedestal brings the total to 49.2 m.
  - The dome centre is from OSM way 235797552. Its 29 m radius is measured on satellite imagery; OSM's 31.8 m is too large.
- **Heading:** from the OSM footprint. The long axis is rotated 37.15° clockwise from east. The two facade scans fit it to an ICP rms of 0.5 m.
- **Simplified or omitted:**
  - The stork sculpture on the dome is left out (only its pedestal is modelled).
  - Ornament reliefs, glazing detail, the surrounding plazas, gardens and terrain are also left out.
  - The columns are simplified to engaged round shafts; the real flared capitals are not modelled.
- **Legal.** Before submitting, check the Yandex terms: https://yandex.ru/legal/maps_mobile_agreement/
