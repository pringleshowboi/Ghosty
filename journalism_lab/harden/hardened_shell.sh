#!/bin/bash
set -euo pipefail
export HISTFILE=/dev/null
unset HISTFILE
export HISTSIZE=0
export HISTFILESIZE=0
set +o history
shopt -u histappend || true
echo "history off"
