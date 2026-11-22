#!/bin/bash
# cutout.sh <local_src> <out_path>
#
# Remove the background from a generated pose sheet and write a transparent PNG.
#
# The generator always paints on a flat white backdrop, so the sheets are cut
# out afterwards instead of asking the model for transparency (it paints a
# fake checkerboard instead of real alpha).
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: cutout.sh <local_src> <out_path>" >&2
  exit 2
fi

src="$1"
out="$2"

url=$(mcode-tools upload_temp_url "$src" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['temp_url'])")

res=$(mcode-tools connector call connector__matrix__remove_image_background \
  --args "{\"image_url\":\"$url\"}")

node=$(printf '%s' "$res" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('node_id',''))")

if [ -z "$node" ]; then
  echo "cutout failed, no node_id in response: $res" >&2
  exit 1
fi

url2=$(mcode-tools get_asset_url "$node" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['download_url'])")

curl -sL "$url2" -o "$out"

python3 - "$out" <<'PY'
import sys
from PIL import Image
p = sys.argv[1]
im = Image.open(p)
alpha = im.getchannel("A")
print(f"saved {p} {im.size} {im.mode} opaque_px={sum(1 for a in alpha.getdata() if a > 8)}")
PY
