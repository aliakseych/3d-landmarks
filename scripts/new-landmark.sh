#!/usr/bin/env bash
# Scaffold a new landmark: local capture/work folders + a models/<slug>/README.md stub.
# usage: scripts/new-landmark.sh <slug> ["Display name"]
set -euo pipefail
slug=${1:?usage: new-landmark.sh <slug> [\"Display name\"]}
name=${2:-$slug}
[[ $slug =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "slug must be lowercase kebab-case: $slug" >&2; exit 1; }

root=$(cd "$(dirname "$0")/.." && pwd)
readme="$root/models/$slug/README.md"
[[ -e $readme ]] && { echo "models/$slug already exists" >&2; exit 1; }

mkdir -p "$root/temp-captures/$slug" "$root/work/$slug" "$root/models/$slug/yandex"
SLUG=$slug NAME=$name awk '{gsub(/\{\{SLUG\}\}/, ENVIRON["SLUG"]); gsub(/\{\{NAME\}\}/, ENVIRON["NAME"]); print}' \
  "$root/scripts/templates/landmark-README.md" > "$readme"

cat <<EOF
created:
  temp-captures/$slug/   put the raw photos here (gitignored)
  work/$slug/            pipeline scratch (gitignored)
  models/$slug/README.md fill in after building the models
next: .omp/skills/photogrammetry-model/SKILL.md, step 1
EOF
