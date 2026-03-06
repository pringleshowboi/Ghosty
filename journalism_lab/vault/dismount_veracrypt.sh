#!/bin/bash
set -e
VERA_MOUNT="${VERACRYPT_MOUNT:-/mnt/ghost_vault}"
veracrypt --text --dismount "$VERA_MOUNT"
