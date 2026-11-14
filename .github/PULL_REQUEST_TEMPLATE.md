## What

<!-- Landmark added/updated, viewer change, pipeline change -->

## Checklist

- [ ] Binaries are in LFS (`git lfs ls-files` lists every new `.glb/.obj/.fbx/.jpg/.png`)
- [ ] No raw captures, `work/`, `temp-*` or `viewer/public/models/` files
- [ ] Own photos have EXIF stripped (`exiftool -gps:all <file>` prints nothing)
- [ ] New landmark: `validate.py` passes, `gltf-validator` reports 0 errors, `models/<slug>/README.md` filled in
- [ ] New landmark: added to `viewer/src/data/` with at most 2 credited photos
- [ ] `pnpm build` passes in `viewer/`
- [ ] I agree my code is MIT-licensed and my models and renders are CC BY 4.0
