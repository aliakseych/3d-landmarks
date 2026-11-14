# 3D Landmarks

Open 3D models of Tashkent landmarks, built from phone photos with photogrammetry. Each landmark ships as:

- a **textured master** (`.glb`) for viewing and sharing, once its photos reconstruct cleanly (see the table);
- a **Yandex Maps 3D** submission model (`.glb` / `.obj` / `.fbx`, ≤ 15,000 triangles, no textures, watertight, georeferenced).

**Viewer:** https://aliakseych.github.io/3d-landmarks/

## Landmarks

| Slug | Landmark | Master | Yandex model |
|---|---|---|---|
| [`amir-temur`](models/amir-temur/) | Amir Temur monument | 137k tris, 4K texture | 14.2k tris |
| [`forums-palace`](models/forums-palace/) | Palace of International Forums "Uzbekistan" | pending (NE/SW facades need a recapture) | 7.4k tris |

## Repository layout

| Path | Contents | In git |
|---|---|---|
| `models/<slug>/` | Deliverables: `<slug>.glb`, `<slug>.json` (lat/lon, dimensions, axes), `yandex/`, `README.md` | yes (binaries via LFS) |
| `viewer/` | Static web viewer (Vite + React + three.js), deployed to GitHub Pages | yes |
| `.omp/skills/` | Pipeline: photogrammetry (`photogrammetry-model`) and Yandex conversion (`yandex-maps-3d-model`) | yes |
| `scripts/` | Repo helpers, e.g. `new-landmark.sh` | yes |
| `temp-captures/<slug>/` | Raw HEIC/MOV captures (carry GPS EXIF) | **no**, local only |
| `work/<slug>/` | Pipeline scratch (staged photos, Object Capture output, QA renders) | **no** |

Models use metres and are centred on the base. In glTF, +Y is up, +X is east and −Z is north. Each `<slug>.json` holds the WGS84 lat/lon of the origin.

## Getting the models

Binary files are stored in [Git LFS](https://git-lfs.com):

```sh
git lfs install
git clone https://github.com/aliakseych/3d-landmarks.git
```

Single files can also be downloaded from the viewer or from the GitHub file page ("Download raw file").

## Running the viewer locally

```sh
cd viewer
pnpm install
pnpm dev      # copies ../models into public/models, then starts Vite
pnpm build    # static site in viewer/dist
```

## Adding a landmark

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: `scripts/new-landmark.sh <slug>`, put photos in `temp-captures/<slug>/`, run the two pipeline skills, then add the place to `viewer/src/data/`.

## License

- **Code** (viewer, scripts, pipeline): [MIT](LICENSE).
- **3D models, model metadata and renders** in `models/`: [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Credit: "3D Landmarks by Alex Sayfi and contributors".
- **Third-party photos** in `viewer/public/photos/` keep their own Wikimedia Commons licences; the author and licence are shown next to each photo in the viewer.

The monuments themselves may be subject to local freedom-of-panorama rules. Check the [Yandex Maps terms](https://yandex.ru/legal/maps_mobile_agreement/) before you submit a model.

[Contributing](CONTRIBUTING.md) · [Contributors](CONTRIBUTORS.md) · [Code of Conduct](CODE_OF_CONDUCT.md) · [Security](SECURITY.md)
