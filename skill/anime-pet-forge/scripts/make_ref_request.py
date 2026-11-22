#!/usr/bin/env python3
"""Build the character-reference image request for a pet.

The reference image is the single source of truth for the character's
identity: every pose sheet is generated with it attached, so the chibi
proportions, palette, outfit and outline stay locked across all 73 frames.

Usage:
    python3 make_ref_request.py --char <char.json> [--out req/ref.json]

The reference prompt is a *text-only* design sheet. It must fully describe
the character, because nothing else constrains the model's identity.
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True, help="path to char.json")
    ap.add_argument("--out", required=True, help="output request json path")
    args = ap.parse_args()

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    ref = cfg["reference"]
    request = {
        "prompt": ref["prompt"],
        "aspect_ratio": ref.get("aspect_ratio", "3:4"),
        "area": ref.get("area", "4K"),
        "output_file": ref.get("output_file", "character-reference"),
        "n": 1,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"requests": [request]}, f, ensure_ascii=False, indent=1)

    print(f"wrote {args.out} -> {request['output_file']} "
          f"({request['aspect_ratio']}, {len(request['prompt'])} prompt chars)")


if __name__ == "__main__":
    sys.exit(main())
