#!/usr/bin/env bash
#
# Regenerate the diagrams in diagrams/svg/ from architecture.dsl.
# Requires Docker only. Run from anywhere:
#
#   documentation/architecture/update-diagrams.sh
#
# Images are pinned by digest so every machine produces the same SVGs.
set -euo pipefail

STRUCTURIZR="structurizr/structurizr@sha256:721136283c2f9cf1ba69037bc9de136c579d66fdcb2d771cb60546ec68def1a5"
PLANTUML="plantuml/plantuml@sha256:d08610df482510844382caa4e016ba2bf7e3231f630f02ee12f250f3416c62b1"   # 1.2026.8

cd "$(dirname "$0")"   # documentation/architecture
DIR="$PWD"
trap 'rm -rf "$DIR/diagrams/puml"' EXIT

echo "==> Exporting views from architecture.dsl"
rm -rf diagrams/puml
if ! out=$(docker run --rm -v "$DIR":/w "$STRUCTURIZR" \
      export -workspace /w/architecture.dsl -format plantuml/structurizr -output /w/diagrams/puml 2>&1) \
   || grep -q "Exception" <<<"$out"; then
  echo "$out" | grep -i "exception" >&2
  echo "Export failed: fix architecture.dsl and try again." >&2
  exit 1
fi

echo "==> Rendering SVGs"
docker run --rm -v "$DIR/diagrams":/d "$PLANTUML" -tsvg -o /d/svg /d/puml/
# Drop the "structurizr-" prefix so the image links in architecture.md keep working.
for f in diagrams/svg/structurizr-*.svg; do mv "$f" "${f/structurizr-/}"; done

echo "Done: diagrams/svg/"
