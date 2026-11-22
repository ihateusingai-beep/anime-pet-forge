#!/bin/bash
# fetch_asset.sh <node_id> <out_path>
#
# Download a generated asset from the image-generation service by node id.
# The generation call returns a node id, not a file -- this turns it into bytes.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: fetch_asset.sh <node_id> <out_path>" >&2
  exit 2
fi

node="$1"
out="$2"

url=$(mcode-tools get_asset_url "$node" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['download_url'])")

curl -sL "$url" -o "$out"

python3 - "$out" <<'PY'
import sys
from PIL import Image
p = sys.argv[1]
im = Image.open(p)
print(f"saved {p} {im.size} {im.mode}")
PY
