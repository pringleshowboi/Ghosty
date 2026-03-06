#!/bin/bash
set -e
VC_CONTAINER="${VC_CONTAINER:-/path/to/container.hc}"
VERA_MOUNT="${VERACRYPT_MOUNT:-/mnt/ghost_vault}"
mkdir -p "$VERA_MOUNT"
veracrypt --text --mount "$VC_CONTAINER" "$VERA_MOUNT"
