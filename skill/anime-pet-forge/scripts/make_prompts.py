#!/usr/bin/env python3
"""Write prompts.json — the verbatim record of every prompt.

The record is what you paste when you need to regenerate exactly one sheet
without touching the rest, and what you read when you want to know what was
actually sent.

The text is produced by the *same* build_prompt() the request builder uses,
so the record can never drift from what would be sent.

Usage:
    python3 make_prompts.py --char pets/my-pet/char.json --out pets/my-pet/prompts.json
    python3 make_prompts.py --char pets/my-pet/char.json --out prompts.json \
            --verify req            # cross-check against the generated req/*.json
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_batch_request import build_prompt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verify", metavar="REQ_DIR",
                    help="compare the record against the request files in this directory")
    args = ap.parse_args()

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    record = {"reference": cfg["reference"], "sheets": {}}
    for key in cfg["sheet_order"]:
        sheet = cfg["sheets"][key]
        record["sheets"][key] = {
            "prompt": build_prompt(cfg, sheet),
            "aspect_ratio": sheet["aspect_ratio"],
            "output_file": "sheet-" + key,
        }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"wrote {args.out} ({len(record['sheets'])} sheets + reference)")

    if not args.verify:
        return 0

    # cross-check the record against whatever request files already exist.
    # A sheet may legitimately have more than one request file: regenerating a
    # sheet leaves the old request behind, and the old prompt is then
    # superseded rather than wrong. Only a sheet with no matching request
    # anywhere is a real failure.
    matched = {k: 0 for k in record["sheets"]}
    seen = {k: 0 for k in record["sheets"]}
    for path in sorted(glob.glob(os.path.join(args.verify, "*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for req in data.get("requests", []):
            out_file = req.get("output_file", "")
            if not out_file.startswith("sheet-"):
                continue
            key = out_file[len("sheet-"):]
            entry = record["sheets"].get(key)
            if entry is None:
                print(f"  [FAIL] {path}: sheet-{key} is not in char.json")
                continue
            seen[key] += 1
            if entry["prompt"] == req["prompt"]:
                matched[key] += 1
            elif entry["aspect_ratio"] != req.get("aspect_ratio"):
                print(f"  [FAIL] {path}: sheet-{key} aspect differs from the record")

    failures = 0
    for key in record["sheets"]:
        if seen[key] == 0:
            continue
        if matched[key] == 0:
            failures += 1
            print(f"  [FAIL] sheet-{key}: no request file matches the record "
                  f"({seen[key]} file(s) found)")
        elif matched[key] < seen[key]:
            print(f"  [info] sheet-{key}: {matched[key]}/{seen[key]} request file(s) "
                  f"match — the rest are superseded earlier attempts")

    total_seen = sum(seen.values())
    print(f"verified {total_seen} request(s) against the record, {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
