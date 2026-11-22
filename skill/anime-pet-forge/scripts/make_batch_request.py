#!/usr/bin/env python3
"""Build a pose-sheet batch request for a pet.

Every pose sheet is generated as one multi-panel sprite sheet against the
character reference image. A "batch" is just a group of sheets sent in one
image-generation call, so a new pet needs fewer round trips.

Usage:
    python3 make_batch_request.py --char <char.json> --batch 1 \
        --ref-url <temporary reference url> --out req/batch1.json

The reference URL is a *temporary* signed URL (usually ~1 hour). Re-upload
the reference before every batch -- an expired URL silently produces a
sheet with a different character.
"""
import argparse
import json
import os
import sys


def build_prompt(cfg, sheet):
    """Assemble one sheet prompt from char.json.

    Blocks are joined with a blank line. A sheet may override the grid header,
    the character block or the ground block, because a pet is sometimes built
    from sheets that were written with slightly different wording.

    `note` is optional: omit the key entirely when the sheet has no note
    block, keep it as "" when the sheet had an empty note block. The two are
    not the same prompt.
    """
    prompts = cfg["prompts"]
    cols, rows = sheet["cols"], sheet["rows"]
    n = cols * rows

    grid = sheet.get("grid_header") or (
        f"Layout: a sprite sheet of {cols} columns by {rows} rows = {n} equal panels, "
        f"read left to right, top row first, then bottom row."
    )
    character = sheet.get("character_prompt") or prompts["character"]
    ground = sheet.get("ground_prompt") or prompts["ground"]
    background = sheet.get("background_prompt") or prompts["background"]

    blocks = [grid, character, "\n".join(sheet["panels"])]
    if "note" in sheet:
        blocks.append(sheet["note"])
    blocks.append(ground)
    if prompts.get("global_note"):
        blocks.append(prompts["global_note"])
    blocks.append(background)
    return "\n\n".join(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--batch", required=True, help="batch number, as a key in char.json batches")
    ap.add_argument("--ref-url", help="temporary url of the character reference image")
    ap.add_argument("--ref-mime", default="image/jpeg",
                    help="mime type of the reference image (default image/jpeg)")
    ap.add_argument("--out", help="output request json path; omit with --print-prompt")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the prompts to stdout instead of writing a request "
                         "file — for reviewing the text before you spend a generation")
    args = ap.parse_args()

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    batches = cfg["batches"]
    key = str(args.batch)
    if key not in batches:
        sys.exit(f"unknown batch {key!r}; available: {sorted(batches)}")
    sheet_keys = batches[key]

    if args.print_prompt:
        for sk in sheet_keys:
            sheet = cfg["sheets"][sk]
            print(f"===== sheet-{sk}  ({sheet['aspect_ratio']}) =====")
            print(build_prompt(cfg, sheet))
            print()
        return 0

    if not args.ref_url or not args.out:
        sys.exit("need --ref-url and --out (or use --print-prompt)")

    requests = []
    for sk in sheet_keys:
        sheet = cfg["sheets"][sk]
        requests.append({
            "prompt": build_prompt(cfg, sheet),
            "aspect_ratio": sheet["aspect_ratio"],
            "area": sheet.get("area", "4K"),
            "output_file": "sheet-" + sk,
            "n": 1,
            "reference_images": [{"url": args.ref_url, "mime_type": args.ref_mime}],
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"requests": requests}, f, ensure_ascii=False, indent=1)

    print(f"wrote {args.out} -> {sheet_keys}")


if __name__ == "__main__":
    sys.exit(main())
