#!/bin/bash
set -e
DIR="${1:-/mnt/ghost_vault/intake/staging}"
find "$DIR" -type f -print0 | while IFS= read -r -d '' f; do
  mat2 -q "$f" || true
  exiftool -overwrite_original -all= "$f" || true
  shred -u -n 3 -z "$f" || true
done
