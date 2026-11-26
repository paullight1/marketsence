#!/usr/bin/env bash
set -Eeuo pipefail

# Run from anywhere; clone sources into research/upstreams in this repository.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="$ROOT/research/upstreams"
mkdir -p "$DEST"

clone_one() {
  local slug="$1" upstream="$2" sha="$3"
  local dir="$DEST/$slug"
  if [[ -d "$dir/.git" ]]; then
    echo "Already cloned: $slug (skip to protect local edits)"
    return
  fi
  if [[ -e "$dir" ]]; then
    echo "ERROR: $dir exists but is not a git clone; refusing to overwrite" >&2
    return 1
  fi
  echo "Cloning $upstream -> $dir"
  git clone --filter=blob:none --no-checkout "https://github.com/$upstream.git" "$dir"
  git -C "$dir" checkout --detach "$sha"
  echo "Pinned $slug at $sha"
}

clone_one "marketlens" "GipsyDanger-dev/MarketLens" "e1f86ba7dc16b69155e624eb23a37606e8b06f28"
clone_one "geolibre" "opengeos/GeoLibre" "396f015fdcb1b3958994bfc56e1038b4a568b532"
clone_one "geoagent" "opengeos/GeoAgent" "3cff6db6ac5dd96e44c46a1efd5d0890ecfc13cd"
clone_one "geolens" "geolens-io/geolens" "85043fc1037f8a237ea9181a92a928f97f96deb5"
clone_one "goat" "plan4better/goat" "9bcaf8555dd366c1acd6c08dae1c541dcaceda5c"
clone_one "osmnx" "gboeing/osmnx" "af346c03401c3f6960ae84617061fa5108533183"
clone_one "valhalla" "valhalla/valhalla" "4d8b2061b566412ce61eb8a2001b7cfa2392356a"
clone_one "geoai" "opengeos/geoai" "87f187e43eaf888eb52a9b2b6ad45ebe4d409f30"
clone_one "overturemaps-py" "OvertureMaps/overturemaps-py" "e79b5e88d866ef34b41b6b860464fbdc1730aa87"
clone_one "geo-fence" "jackson-marcus/Geo-Fence" "6d10129e3efbacb7120ffa684202a20a43d32f37"
echo "Completed upstream clones. Repositories are excluded from the parent Git index."
