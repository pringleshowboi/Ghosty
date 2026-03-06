#!/bin/bash
set -euo pipefail
export TOR_SOCKS="${TOR_SOCKS:-socks5h://127.0.0.1:9050}"
export http_proxy="$TOR_SOCKS"
export https_proxy="$TOR_SOCKS"
export all_proxy="$TOR_SOCKS"
printf "Tor proxy %s\n" "$TOR_SOCKS"
