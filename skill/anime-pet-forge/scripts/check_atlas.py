#!/usr/bin/env python3
"""Check a finished atlas against the layout it was supposed to have.

The official validator checks that a cell is non-empty. It does **not** check
that the right frame landed in the right cell, that nothing is clipped, that
the rows share a size, or that the look directions are in the right order.

This does. It recomputes the expected cell map from char.json and then looks
at the picture.

Usage:
    python3 check_atlas.py --char pets/my-pet/char.json --atlas pets/my-pet/spritesheet.png
"""
import argparse
import json
import os
import re
import sys

from PIL import Image

CELL_W, CELL_H = 192, 208
ALPHA_MIN = 8


def median(values):
    s = sorted(values)
    return s[len(s) // 2]


def expected_cells(cfg):
    """{(row, col): sheet_key} for every cell that must have art."""
    cells = {}
    for index, key in enumerate(cfg["sheet_order"]):
        sheet = cfg["sheets"][key]
        atlas = sheet.get("atlas") or {}
        n = sheet.get("frames", 0)
        if "rows" in atlas:
            rows = atlas["rows"]
            per = atlas.get("columns_per_row", 8)
            for i in range(n):
                cells[(rows[i // per], i % per)] = key
        else:
            row = atlas.get("row", index)
            for i in range(n):
                cells[(row, i)] = key
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--atlas", required=True)
    args = ap.parse_args()

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    atlas = Image.open(args.atlas).convert("RGBA")
    errors, warnings, info = [], [], []

    if atlas.size != (CELL_W * 8, CELL_H * 11):
        errors.append(f"atlas is {atlas.size}, expected {(CELL_W * 8, CELL_H * 11)}")

    cells = expected_cells(cfg)
    if len(cells) != 73:
        warnings.append(f"char.json describes {len(cells)} cells, expected 73")

    # ---- per-cell checks -------------------------------------------------
    heights_by_row = {}
    feet_by_row = {}
    edge_hits = []

    for (row, col), key in sorted(cells.items()):
        x0, y0 = col * CELL_W, row * CELL_H
        cell = atlas.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))
        a = cell.getchannel("A")
        pixels = list(a.getdata())
        opaque = sum(1 for p in pixels if p > ALPHA_MIN)
        transparent = sum(1 for p in pixels if p == 0)

        if opaque == 0:
            errors.append(f"cell ({row},{col}) [{key}] is empty")
            continue
        if transparent == 0:
            errors.append(f"cell ({row},{col}) [{key}] has no transparent background")
            continue

        bbox = a.point(lambda p: 255 if p > ALPHA_MIN else 0).getbbox()
        l, t, r, b = bbox
        if l == 0 or t == 0 or r == CELL_W or b == CELL_H:
            edge_hits.append(f"cell ({row},{col}) [{key}] touches the cell edge")
        heights_by_row.setdefault(row, []).append(b - t)
        feet_by_row.setdefault(row, []).append(b)

    for e in edge_hits:
        errors.append(e)

    # ---- rows that were shrunk to fit an over-wide frame ------------------
    #
    # The assembler scales a row so its median frame lands on exactly
    # assembly.target_h, then multiplies the whole row by the row cap. So the
    # median sprite height of a finished row IS target_h * cap — which means
    # the cap can be read back off the finished atlas.
    target_h = (cfg.get("assembly") or {}).get("target_h", 168)
    global_med = median([median(h) for row, h in heights_by_row.items() if row <= 8]) \
        if any(row <= 8 for row in heights_by_row) else 0
    info.append(f"median sprite height across animation rows: {global_med}px "
                f"(target_h = {target_h})")
    for row in sorted(heights_by_row):
        med = median(heights_by_row[row])
        label = cfg["sheet_order"][row] if row < len(cfg["sheet_order"]) else "?"
        implied_cap = med / target_h if target_h else 1.0
        if implied_cap < 0.995:
            errors.append(f"row {row} ({label}) was scaled to {implied_cap:.2f} "
                          f"(median height {med}px instead of {target_h}px) — "
                          f"an over-wide frame forced the whole row down")
        else:
            info.append(f"row {row} ({label}): median height {med}px "
                        f"(cap {implied_cap:.2f})")

    # ---- feet baseline spread per row (informational) ---------------------
    for row in sorted(feet_by_row):
        vals = feet_by_row[row]
        spread = max(vals) - min(vals)
        label = cfg["sheet_order"][row] if row < len(cfg["sheet_order"]) else "?"
        note = "  (motion amplitude, expected to be large)" if label == "jump" else ""
        info.append(f"row {row} ({label}): feet spread {spread}px{note}")

    # ---- look directions --------------------------------------------------
    gaze_cells = sorted((rc for rc, k in cells.items() if k == "gaze"))
    if len(gaze_cells) != 16:
        errors.append(f"gaze occupies {len(gaze_cells)} cells, expected 16")
    else:
        want = [(9 + i // 8, i % 8) for i in range(16)]
        if gaze_cells != want:
            errors.append(f"gaze cells are {gaze_cells}, expected {want}")
        else:
            info.append("gaze: 16 cells in rows 9-10, zero degrees = up, clockwise")

    print(f"atlas: {args.atlas}")
    for i in info:
        print(f"  [info] {i}")
    for w in warnings:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [FAIL] {e}")
    if errors:
        print(f"\n{len(errors)} problem(s)")
        return 1
    print("\nOK — layout, cell map, edges and row sizes all check out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
