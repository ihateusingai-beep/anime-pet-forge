#!/bin/bash
# validate.sh <pet-dir>
#
# Run the official MiniMax Pet artwork validator against a pet directory.
#
# The validator ships with the official `minimax-pet` skill. Its install path
# changes between profiles and plugin versions, so it is resolved at runtime
# instead of hardcoded.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: validate.sh <pet-dir>" >&2
  exit 2
fi

pet_dir="$1"

skill_dir=""
for base in "${MINIMAX_HOME:-$HOME/.minimax}" "$HOME/.minimax"; do
  found=$(find "$base" -type d -name minimax-pet -path '*/skills/*' 2>/dev/null | head -1 || true)
  if [ -n "$found" ]; then
    skill_dir="$found"
    break
  fi
done

if [ -z "$skill_dir" ] || [ ! -f "$skill_dir/scripts/validate-art.mjs" ]; then
  echo "could not locate the official minimax-pet skill (validate-art.mjs)" >&2
  echo "install the official MiniMax Pet plugin, then re-run" >&2
  exit 1
fi

echo "validator: $skill_dir/scripts/validate-art.mjs"
node "$skill_dir/scripts/validate-art.mjs" "$pet_dir/pet.json"
