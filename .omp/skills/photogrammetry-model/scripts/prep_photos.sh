#!/usr/bin/env bash
# Stage a landmark's raw photos for objcap + QA without touching the originals.
# usage: prep_photos.sh <rawDir> <workDir> [EXCLUDE_STEM ...]
#   <rawDir> may hold photos directly or per-shot folders (IMG_1141/IMG_1141.HEIC + Live Photo .MOV).
#   <workDir>/images/  hard links to the HEIC/JPG originals (objcap input; keeps EXIF GPS/compass)
#   <workDir>/photos/  display-oriented 1200px JPEGs (overlay QA, contact sheets)
# Exclude blurred shots, close-ups that show no context, and frames dominated by people/cars.
set -euo pipefail
raw=$1 work=$2; shift 2
mkdir -p "$work/images" "$work/photos"
find "$raw" -type f \( -iname '*.heic' -o -iname '*.jpg' -o -iname '*.jpeg' \) | sort | while read -r f; do
  stem=$(basename "${f%.*}")
  for x in "$@"; do [ "$stem" = "$x" ] && continue 2; done
  ln -f "$f" "$work/images/" 2>/dev/null || cp "$f" "$work/images/"
  sips -s format jpeg -s formatOptions 85 -Z 1200 "$f" --out "$work/photos/$stem.jpg" >/dev/null
done
# sips keeps the EXIF Orientation tag instead of rotating pixels; bake it in
python3 - "$work/photos" <<'EOF'
import sys, glob
from PIL import Image, ImageOps
for p in glob.glob(sys.argv[1] + "/*.jpg"):
    im = Image.open(p)
    if im.getexif().get(0x0112, 1) != 1:
        ImageOps.exif_transpose(im).save(p, quality=85)
EOF
echo "images: $(ls "$work/images" | wc -l)  photos: $(ls "$work/photos" | wc -l)"
