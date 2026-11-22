#!/usr/bin/env python3
"""Validate a char.json before you spend a single generation call on it.

Catches the mistakes that fail *silently* later:
  - a sheet key missing or misspelled  -> the frame is simply never drawn
  - frames != len(panels)             -> a cell is left empty
  - two sheets claiming the same atlas row -> one silently overwrites the other
  - a leftover "_copy ..." placeholder from the template
  - a batch that forgets a sheet, or lists one twice
  - gaze not mapped to rows 9 and 10

Usage:
    python3 check_char.py --char pets/my-pet/char.json
"""
import argparse
import json
import sys

REQUIRED_SHEETS = ["idle", "run-right", "run-left", "wave", "jump",
                   "failed", "waiting", "work", "review", "gaze"]
EXPECTED_FRAMES = {"idle": 6, "run-right": 8, "run-left": 8, "wave": 4,
                   "jump": 5, "failed": 8, "waiting": 6, "work": 6,
                   "review": 6, "gaze": 16}
EXPECTED_ANIM_ROW = {"idle": 0, "run-right": 1, "run-left": 2, "wave": 3,
                     "jump": 4, "failed": 5, "waiting": 6, "work": 7,
                     "review": 8}
TOTAL_FRAMES = 73


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    args = ap.parse_args()

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    errors, warnings = [], []

    def err(msg):
        errors.append(msg)

    def warn(msg):
        warnings.append(msg)

    for key in ("id", "displayName", "reference", "prompts", "sheets",
                "batches", "assembly"):
        if key not in cfg:
            err(f"missing top-level key: {key}")

    if not cfg.get("id"):
        err("id is empty")
    if not cfg.get("displayName"):
        err("displayName is empty")

    pet_id = cfg.get("id", "")
    if pet_id and not all(c.islower() or c.isdigit() or c in "._-" for c in pet_id):
        err(f"id {pet_id!r} must match ^[a-z0-9][a-z0-9._-]{{0,79}}$")
    if pet_id == "minimax-original":
        err("id 'minimax-original' is reserved by the plugin")

    prompts = cfg.get("prompts", {})
    for key in ("character", "ground", "background"):
        if not prompts.get(key):
            err(f"prompts.{key} is empty")

    sheets = cfg.get("sheets", {})
    for key in REQUIRED_SHEETS:
        if key not in sheets:
            err(f"missing sheet: {key}")

    for key, sheet in sheets.items():
        where = f"sheets.{key}"
        panels = sheet.get("panels")
        if not isinstance(panels, list) or not panels:
            err(f"{where}.panels is missing or empty")
            continue
        for i, p in enumerate(panels):
            if not isinstance(p, str) or not p.strip():
                err(f"{where}.panels[{i}] is empty")
            elif p.strip().startswith("_") or "_copy" in p.lower():
                err(f"{where}.panels[{i}] still holds a template placeholder: {p[:60]!r}")
        n = sheet.get("frames")
        if n is None:
            err(f"{where}.frames is missing")
        elif n != len(panels):
            err(f"{where}.frames={n} but {len(panels)} panels")
        elif EXPECTED_FRAMES.get(key) is not None and n != EXPECTED_FRAMES[key]:
            err(f"{where}.frames={n}, the v2 spec needs {EXPECTED_FRAMES[key]}")
        cols, rows = sheet.get("cols"), sheet.get("rows")
        if not cols or not rows:
            err(f"{where}.cols/.rows missing")
        elif cols * rows < len(panels):
            err(f"{where}: {cols}x{rows} grid cannot hold {len(panels)} panels")
        if sheet.get("aspect_ratio") is None:
            err(f"{where}.aspect_ratio missing")
        atlas = sheet.get("atlas")
        if not atlas:
            err(f"{where}.atlas missing")
        note = sheet.get("note")
        if note is not None and not isinstance(note, str):
            err(f"{where}.note must be a string")

    # atlas rows must be unique, and the animation rows fixed by the spec
    row_owner = {}
    for key, sheet in sheets.items():
        atlas = sheet.get("atlas") or {}
        if "rows" in atlas:
            for r in atlas["rows"]:
                row_owner.setdefault(r, []).append(key)
        else:
            row_owner.setdefault(atlas.get("row"), []).append(key)
    for row, owners in sorted(row_owner.items(), key=lambda kv: (kv[0] is None, kv[0])):
        if row is None:
            err("a sheet has no atlas row")
        elif len(owners) > 1:
            err(f"atlas row {row} is claimed by {owners}")

    for key, expected in EXPECTED_ANIM_ROW.items():
        sheet = sheets.get(key)
        if sheet and (sheet.get("atlas") or {}).get("row") != expected:
            err(f"sheets.{key}.atlas.row must be {expected} (v2 spec), "
                f"got {(sheet.get('atlas') or {}).get('row')}")

    gaze = sheets.get("gaze")
    if gaze:
        rows = (gaze.get("atlas") or {}).get("rows")
        if rows != [9, 10]:
            err(f"sheets.gaze.atlas.rows must be [9, 10], got {rows}")
        if (gaze.get("atlas") or {}).get("columns_per_row") != 8:
            err("sheets.gaze.atlas.columns_per_row must be 8")

    total = sum(s.get("frames", 0) or 0 for s in sheets.values())
    if total != TOTAL_FRAMES:
        warn(f"total frames = {total}, the v2 spec needs {TOTAL_FRAMES}")

    batches = cfg.get("batches", {})
    covered = []
    for bname, keys in batches.items():
        for k in keys:
            covered.append(k)
            if k not in sheets:
                err(f"batches.{bname} lists unknown sheet {k!r}")
    missing = [k for k in REQUIRED_SHEETS if k not in covered]
    if missing:
        err(f"sheets never generated (no batch covers them): {missing}")
    dupes = [k for k in set(covered) if covered.count(k) > 1]
    if dupes:
        err(f"sheets appear in more than one batch: {dupes}")

    # the reference prompt is the only thing locking the character identity
    ref = cfg.get("reference", {})
    if not ref.get("prompt"):
        err("reference.prompt is empty")
    elif len(ref["prompt"]) < 300:
        warn(f"reference.prompt is only {len(ref['prompt'])} chars — "
             "a thin design sheet gives the model nothing to hold on to")
    if not ref.get("aspect_ratio"):
        warn("reference.aspect_ratio missing")

    print(f"char.json: {args.char}")
    print(f"  sheets        : {len(sheets)}")
    print(f"  total frames  : {total} (spec wants {TOTAL_FRAMES})")
    print(f"  batches       : {len(batches)}")
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [FAIL] {e}")
    if errors:
        print(f"\n{len(errors)} error(s) — fix these before generating anything")
        return 1
    print(f"\nOK{('  (' + str(len(warnings)) + ' warning(s))') if warnings else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
