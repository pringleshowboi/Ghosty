#!/bin/bash
set -euo pipefail

SRC="${1:-/mnt/vault}"
DEST="${2:-$HOME/exports}"
mkdir -p "$DEST"

if [ ! -d "$SRC" ]; then
  echo "Source directory not found: $SRC"
  exit 1
fi

read -s -p "Passphrase: " PASS; echo
read -s -p "Confirm Passphrase: " PASS2; echo
if [ "$PASS" != "$PASS2" ]; then
  echo "Passphrases do not match"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
OUT="$DEST/vault_export_${TS}.tar.xz.gpg"

echo "Creating encrypted archive at $OUT ..."
tar -C "$SRC" -cJf - . \
  | gpg --batch --yes --pinentry-mode loopback --passphrase "$PASS" -c -o "$OUT"

sha256sum "$OUT" > "${OUT}.sha256"
echo "Done."
echo "Archive: $OUT"
echo "SHA256:  $(cut -d' ' -f1 ${OUT}.sha256)"

