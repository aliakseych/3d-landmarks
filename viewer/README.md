# Tashkent landmarks in 3D

Static viewer (Vite + React + three.js) for the photogrammetry models in `../models/`.

```sh
pnpm install
pnpm dev        # http://localhost:5173
pnpm build      # type-check + production build into dist/
pnpm preview    # serve dist/
```

## Syncing models

`pnpm dev` and `pnpm build` first run `scripts/sync-models.mjs`, which copies `../models/**/*.{glb,obj,fbx,json}` into `public/models/` (gitignored, generated). Run `pnpm sync-models` by hand after new models land. Missing files show an "not available yet" state in the viewer; nothing is faked.

## Notes

- `base: './'` and hash routing (`#amir-temur/yandex`) make `dist/` work under any sub-path (GitHub Pages).
- Real-world photos in `public/photos/<slug>/` are from Wikimedia Commons; credits and licences are in `src/data/photos.ts` and shown in the page.
- Places are defined in `src/data/places.ts`; adding one means adding an entry and its photos.
