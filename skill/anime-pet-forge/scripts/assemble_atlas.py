#!/usr/bin/env python3
"""Assemble a MiniMax Pet v2 atlas (1536x2288, 8 cols x 11 rows, 192x208 cells).

Two modes:

  --from-sheets <dir>   the generation pipeline. Reads the background-removed
                        pose sheets (sheet-<key>-cut.png), slices them back into
                        panels, normalises apparent size and foot baseline,
                        and pastes them into the atlas grid. Use this when the
                        4K source sheets are still around.

  --from-frames <dir>   the reproducible path. Reads the per-cell 192x208 PNGs
                        named <key>_<row><col>.png and pastes them straight into
                        the grid. This reproduces the atlas pixel for pixel and
                        needs no image generation at all.

Usage:
    python3 assemble_atlas.py --char <char.json> --out <pet-dir> \
        [--from-sheets <dir> | --from-frames <dir>] [--dump <dir>]
"""
import argparse
import json
import os
import re
import sys

from PIL import Image

CELL_W, CELL_H = 192, 208
COLS, ROWS = 8, 11
ALPHA_MIN = 8

CELL_RE = re.compile(r"^(.+)_(\d+)\.png$")


# ---------------------------------------------------------------- primitives

def mask_of(img):
    return img.getchannel("A").point(lambda a: 255 if a > ALPHA_MIN else 0)


def median(values):
    s = sorted(values)
    return s[len(s) // 2]


def bands(profile, expected):
    """Spans of non-empty rows/cols, or None when the count does not match."""
    peak = max(profile) if profile else 0
    if peak == 0:
        return None
    # relative threshold: a faint full-width line must not count as content
    thresh = max(1, peak * 0.02)
    spans, start = [], None
    for i, v in enumerate(profile):
        if v > thresh and start is None:
            start = i
        elif v <= thresh and start is not None:
            spans.append((start, i))
            start = None
    if start is not None:
        spans.append((start, len(profile)))
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] <= 6:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(s)
    return merged if len(merged) == expected else None


def even_spans(lo, hi, n):
    step = (hi - lo) / n
    return [(int(lo + i * step), int(lo + (i + 1) * step)) for i in range(n)]


def panel_grid(img, cols, rows):
    """rows x cols list of PIL images, one per panel of the sheet."""
    m = mask_of(img)
    W, H = img.size
    col_prof = [sum(1 for y in range(0, H, 3) if m.getpixel((x, y)) > 0) for x in range(W)]
    row_prof = [sum(1 for x in range(0, W, 3) if m.getpixel((x, y)) > 0) for y in range(H)]

    cb = bands(col_prof, cols)
    rb = bands(row_prof, rows)
    if cb is None or rb is None:
        bbox = m.getbbox()
        if bbox is None:
            raise SystemExit("empty sheet")
        x0, y0, x1, y1 = bbox
        if cb is None:
            cb = even_spans(x0, x1, cols)
        if rb is None:
            rb = even_spans(y0, y1, rows)
        print(f"    [grid] uneven panels -> even split cols={len(cb)} rows={len(rb)}")
    return [[img.crop((x0, y0, x1, y1)) for (x0, x1) in cb] for (y0, y1) in rb]


def frame_stats(panel):
    m = mask_of(panel)
    bbox = m.getbbox()
    if bbox is None:
        return None, 0
    area = sum(1 for p in panel.getchannel("A").getdata() if p > ALPHA_MIN)
    return bbox, area


# ------------------------------------------------------------ sheet pipeline

def build_row_from_sheet(sheet, sheets_dir, target_h, baseline, margin):
    """Slice one pose sheet into normalised frames."""
    fname = sheet.get("sheet_file") or ("sheet-%s-cut.png" % sheet["key"])
    img = Image.open(os.path.join(sheets_dir, fname)).convert("RGBA")
    grid = panel_grid(img, sheet["cols"], sheet["rows"])
    flat = [grid[r][c] for r in range(sheet["rows"]) for c in range(sheet["cols"])]
    flat = flat[: sheet["frames"]]

    stats = [frame_stats(p) for p in flat]
    boxes = [b for b, a in stats if b]
    heights = [b[3] - b[1] for b in boxes]
    med_h = median(heights)
    base = target_h / med_h

    if sheet.get("fixed_scale"):
        scales = [base] * len(flat)
    else:
        lo = sheet.get("clamp_low", 0.9)
        hi = sheet.get("clamp_high", 1.1)
        scales = [base * max(lo, min(hi, med_h / h)) for h in heights]

    # never let a frame exceed the cell
    cap = 1.0
    for (bbox, area), s in zip(stats, scales):
        if bbox is None:
            continue
        w = (bbox[2] - bbox[0]) * s
        h = (bbox[3] - bbox[1]) * s
        cap = min(cap, (CELL_W - 2 * margin) / w, (CELL_H - 2 * margin) / h)
    scales = [s * cap for s in scales]

    feet = [b[3] for b in boxes]
    m_feet = median(feet)

    frames = []
    for panel, (bbox, area), s in zip(flat, stats, scales):
        if bbox is None:
            frames.append(None)
            continue
        x0, y0, x1, y1 = bbox
        w = max(1, int(round((x1 - x0) * s)))
        h = max(1, int(round((y1 - y0) * s)))
        art = panel.crop(bbox).resize((w, h), Image.LANCZOS)
        lift = (m_feet - y1) * s
        frames.append({"art": art, "lift": lift})
    return frames, cap


def place_frame(art, lift, baseline, margin):
    x = (CELL_W - art.size[0]) // 2
    y = baseline - art.size[1] - int(round(lift))
    y = max(margin, min(CELL_H - margin - art.size[1], y))
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    cell.paste(art, (x, y), art)
    return cell


def atlas_targets(sheet, index):
    """Where this sheet's frames land in the 8x11 grid."""
    spec = sheet.get("atlas", {})
    n = sheet.get("frames", 0)
    if "rows" in spec:
        rows = spec["rows"]
        per = spec.get("columns_per_row", COLS)
        return [(rows[i // per], i % per) for i in range(n)]
    return [(spec.get("row", index), i) for i in range(n)]


# ------------------------------------------------------------------- drivers

def assemble_from_sheets(cfg, sheets_dir, dump_dir=None):
    asm = cfg.get("assembly", {})
    target_h = asm.get("target_h", 168)
    baseline = asm.get("baseline", 196)
    margin = asm.get("margin", 4)

    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))
    for index, key in enumerate(cfg["sheet_order"]):
        sheet = dict(cfg["sheets"][key])
        sheet["key"] = key
        frames, cap = build_row_from_sheet(sheet, sheets_dir, target_h, baseline, margin)
        sizes = [f["art"].size for f in frames if f]
        print(f"[{index}] {key:10s} {len(frames):2d} frames  cap={cap:.2f}  "
              f"h={min(s[1] for s in sizes)}-{max(s[1] for s in sizes)}  "
              f"w={min(s[0] for s in sizes)}-{max(s[0] for s in sizes)}")

        targets = atlas_targets(sheet, index)
        for fr, (row, col) in zip(frames, targets):
            if fr is None:
                continue
            cell = place_frame(fr["art"], fr["lift"], baseline, margin)
            atlas.paste(cell, (col * CELL_W, row * CELL_H))
            if dump_dir:
                os.makedirs(dump_dir, exist_ok=True)
                cell.save(os.path.join(dump_dir, f"{key}_{row}{col}.png"))
    return atlas


def assemble_from_frames(frames_dir):
    """Paste the per-cell 192x208 PNGs straight into the grid."""
    atlas = Image.new("RGBA", (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))
    count = 0
    for fn in sorted(os.listdir(frames_dir)):
        m = CELL_RE.match(fn)
        if not m:
            continue
        row, col = int(m.group(2)[:-1]), int(m.group(2)[-1])
        cell = Image.open(os.path.join(frames_dir, fn)).convert("RGBA")
        if cell.size != (CELL_W, CELL_H):
            raise SystemExit(f"{fn} is {cell.size}, expected {(CELL_W, CELL_H)}")
        atlas.paste(cell, (col * CELL_W, row * CELL_H))
        count += 1
    print(f"pasted {count} cells from {frames_dir}")
    return atlas


def write_outputs(cfg, atlas, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out_png = os.path.join(out_dir, "spritesheet.png")
    atlas.save(out_png, "PNG", optimize=True)
    size = os.path.getsize(out_png)
    print(f"saved {out_png} {atlas.size} {size / 1024 / 1024:.2f} MiB")
    if size > 8 * 1024 * 1024:
        print("WARNING: over the 8 MiB generation budget", file=sys.stderr)

    pet = {
        "id": cfg["id"],
        "displayName": cfg["displayName"],
        "description": cfg.get("description", ""),
        "spritesheetPath": "spritesheet.png",
        "spriteVersionNumber": cfg.get("spriteVersionNumber", 2),
    }
    out_json = os.path.join(out_dir, "pet.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(pet, f, ensure_ascii=False, indent=2)
    print(f"saved {out_json}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--out", required=True, help="output directory for spritesheet.png + pet.json")
    ap.add_argument("--from-sheets", help="directory holding sheet-<key>-cut.png files")
    ap.add_argument("--from-frames", help="directory holding <key>_<row><col>.png cell files")
    ap.add_argument("--dump", help="also write the per-cell frames here")
    args = ap.parse_args()

    if not args.from_sheets and not args.from_frames:
        sys.exit("need --from-sheets or --from-frames")

    with open(args.char, encoding="utf-8") as f:
        cfg = json.load(f)

    if args.from_frames:
        atlas = assemble_from_frames(args.from_frames)
    else:
        atlas = assemble_from_sheets(cfg, args.from_sheets, args.dump)

    write_outputs(cfg, atlas, args.out)


if __name__ == "__main__":
    sys.exit(main())
