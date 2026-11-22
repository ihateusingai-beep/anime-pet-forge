---
name: anime-pet-forge
description: Forge original anime-style desktop pets for MiniMax Pet v2 — a 1536x2288 RGBA spritesheet (8x11 grid of 192x208 cells, 9 animation tracks + 16 look directions) plus pet.json. Use when creating a new chibi/anime pet, porting a character into the MiniMax Pet app, rebuilding a pet atlas from per-cell frames, or fixing a pet whose cells are clipped, mis-scaled or mis-aligned.
---

# Anime Pet Forge

Turn a character concept into a validated, importable MiniMax Pet.

The hard part of this job is **not** drawing — it is making 73 independently
generated frames look like one character, at one size, on one baseline, inside
a fixed grid. This skill exists to make that mechanical instead of artisanal.

Work with the official `minimax-pet` skill alongside this one: it owns the
**atlas specification** and the **validator**. This skill owns the
**production pipeline** — reference sheet, pose sheets, cut-out, assembly.

---

## The pipeline

```text
  char.json
     │
     ├─(1) make_ref_request.py ──► generate ──► character reference image
     │                                        (single source of truth for identity)
     │
     ├─(2) make_batch_request.py ──► generate ──► 10 pose sheets
     │                                        (idle/run×2/wave/jump/failed/
     │                                         waiting/work/review/gaze)
     │
     ├─(3) fetch_asset.sh + cutout.sh ──► transparent per-sheet PNGs
     │
     ├─(4) assemble_atlas.py ──► spritesheet.png (1536×2288) + pet.json
     │
     ├─(5) check_atlas.py ──► layout / row-size / gaze-order check
     │
     ├─(6) validate.sh ──► official validator
     │                     │
     └─(7) import through the MiniMax Pet app
```

`check_char.py` guards the front of the pipeline: a missing sheet or a
mismatched frame count fails silently later, so check the config before you
spend a generation call.

### (0) Check the config

```sh
python3 scripts/check_char.py --char pets/my-pet/char.json
```

Catches a missing sheet, a frame count that disagrees with the panel list, two
sheets claiming the same atlas row, a batch that forgets a sheet, and leftover
template placeholders. Every one of those fails *silently* later — the sheet
is simply never drawn, or it is drawn over something else.

### (1) Character reference

```sh
python3 scripts/make_ref_request.py --char pets/my-pet/char.json --out req/ref.json
mcode-tools connector call connector__matrix__generate_image --args-file req/ref.json
```

The reference image is a **text-only design sheet** (unless the user supplies a
reference image themselves). It must fully describe the character — the model
has nothing else to go on. Lock: chibi proportions, hair silhouette, eye
colour and shape, outfit with every colour accent, outline colour, art style.

### (2) Pose sheets

The reference image is uploaded to a **temporary signed URL** (usually ~1 hour).
Re-upload it before **every** batch — an expired URL silently yields a sheet
with a different character.

```sh
url=$(mcode-tools upload_temp_url pets/my-pet/refs/reference.jpg \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['temp_url'])")
python3 scripts/make_batch_request.py --char pets/my-pet/char.json \
        --batch 1 --ref-url "$url" --ref-mime image/jpeg --out req/batch1.json
mcode-tools connector call connector__matrix__generate_image --args-file req/batch1.json
```

Repeat for every batch in `char.json` → `batches`. Each sheet is one
multi-panel image; the model draws the whole sheet, not individual frames.

To read the text before spending a generation:

```sh
python3 scripts/make_batch_request.py --char pets/my-pet/char.json \
        --batch 1 --print-prompt
```

Write the verbatim record of every prompt as you go, and cross-check it
against what was actually sent:

```sh
python3 scripts/make_prompts.py --char pets/my-pet/char.json \
        --out pets/my-pet/prompts.json --verify req
```

### (3) Download and cut out

The generator paints on flat white; it cannot be trusted to emit real alpha.
Cut every sheet out afterwards:

```sh
bash scripts/fetch_asset.sh <node_id> sheets/sheet-idle.jpg
bash scripts/cutout.sh sheets/sheet-idle.jpg sheets/sheet-idle-cut.png
```

### (4) Assemble

```sh
python3 scripts/assemble_atlas.py --char pets/my-pet/char.json \
        --from-sheets sheets --out pets/my-pet --dump pets/my-pet/frames
```

`--from-sheets` is the generation path: it slices the 4K sheets back into
panels, normalises apparent size against the row median, aligns every frame
to a shared foot baseline, and scales the whole row down if any frame would
otherwise touch the cell edge.

`--from-frames` is the reproducible path:

```sh
python3 scripts/assemble_atlas.py --char pets/my-pet/char.json \
        --from-frames pets/my-pet/frames --out pets/my-pet
```

It pastes the per-cell 192×208 PNGs straight into the grid. This reproduces
the atlas **pixel for pixel** with no image generation at all, so a finished
pet can be shipped with its `frames/` directory and rebuilt by anyone.

### (5) Check the atlas yourself

```sh
python3 scripts/check_atlas.py --char pets/my-pet/char.json \
        --atlas pets/my-pet/spritesheet.png
```

The official validator only asks "is this cell non-empty". It cannot tell you
that the wrong frame landed in the wrong cell, that a row was scaled down, or
that the look directions are in the wrong order. This recomputes the expected
cell map from `char.json` and checks the picture against it.

The check that matters most: the assembler scales every row so its median
frame lands on exactly `assembly.target_h`, then multiplies the row by its
cap. So **a finished row's median height is `target_h × cap`** — a row
measuring 149 px instead of 168 px was scaled to 0.89 to fit an over-wide
frame, and the character is now visibly smaller in that animation. The
official validator reports `ok: true` for that atlas.

### (6) Validate

```sh
bash scripts/validate.sh pets/my-pet
```

Runs the official validator (resolved from the installed `minimax-pet` skill,
never hardcoded). Exit 0 and `ok: true` is the bar — but it is not the only
bar. Run `check_atlas.py` too, and look at the picture.

### (7) Import

Import `pet.json` **and** `spritesheet.png` through the app's own import
panel. Never write the Host data directory, never call a private endpoint,
never patch the installed package. Use a **new pet id** unless the user
explicitly confirms replacing an existing one.

---

## Configuration: `char.json`

One file per pet, describing everything the pipeline needs.

| Field | Meaning |
|---|---|
| `id`, `displayName`, `description` | written into `pet.json` |
| `reference` | the text-only character design prompt + aspect ratio |
| `prompts.character` | the "Picture 1 is the exact character to reproduce…" block reused in every sheet |
| `prompts.ground` | the "stands on the same horizontal ground line" block |
| `prompts.background` | the pure-white-background block |
| `prompts.global_note` | optional extra constraint appended to every sheet (e.g. a hair silhouette rule) |
| `sheets.<key>` | `aspect_ratio`, `cols`, `rows`, `frames`, `panels[]`, `note`, and the assembly tuning (`clamp_low`, `clamp_high`, `fixed_scale`, `atlas`) |
| `batches` | which sheets go into which generation call |
| `assembly` | `target_h`, `baseline`, `margin` |

A sheet may override `grid_header`, `character_prompt`, `ground_prompt` or
`background_prompt` when it was written with different wording than the rest
of the pet. Omit the `note` key entirely when a sheet has no note block; keep
it as `""` when it had an empty one — those are different prompts.

See `references/character-config.md` for the full schema and
`templates/char.example.json` for a starting point.

---

## Things that will bite you

Read `references/pitfalls.md` before your first generation run. The short list:

1. **A character that overflows its cell is silently scaled down.** A cat with
   a streaming tail ends up 1.4× wider than tall, so the assembler shrinks the
   whole row to fit and the pet suddenly looks smaller than in every other
   row. Constrain the silhouette in the prompt and regenerate.
2. **Long hair must be told to hang, not fan.** "Long straight hair" alone
   makes the model spread it sideways.
3. **Sheet panels are not evenly sized.** The assembler finds the real panel
   boundaries from the alpha mask and falls back to an even split — but a
   sheet with a stray full-width line (a faint horizon) breaks the column
   detection. Generate on pure white with no horizon.
4. **The reference URL expires.** See (2).
5. **Never commit `req/*.json`.** They embed signed OSS URLs with a
   credential and a signature. They are short-lived, but they are still
   credentials in a file.
6. **The validator does not judge art.** It checks metadata, pixels, layout
   and non-empty cells. It cannot tell you the character is inconsistent or
   that the gaze directions are wrong — and it reports `ok: true` for an atlas
   whose run row was scaled down to 0.89.

   `scripts/check_atlas.py` catches the scaled row for you, but only a human
   catches the character drift. Look at the atlas yourself.

---

## Windows (win32) platform notes

The Python scripts (`make_ref_request.py`, `make_batch_request.py`,
`assemble_atlas.py`) are cross-platform as long as Python 3 with Pillow is
installed — `python3` may be `python` on Windows.

The three `.sh` helpers (`fetch_asset.sh`, `cutout.sh`, `validate.sh`) need
bash. On Windows, either run them under Git Bash / WSL, or port the three
one-liners to PowerShell — each is only a `mcode-tools` call piped through
`python3 -c` plus a `curl`/`Invoke-WebRequest` download. Nothing else in the
pipeline is platform-specific.

`mcode-tools` itself ships with MiniMax Code and is expected on `PATH` for
every platform.

---

## Layout of a finished pet

```text
pets/my-pet/
  pet.json          # metadata for the app
  spritesheet.png   # 1536×2288, 8-bit RGBA, non-interlaced, ≤ 8 MiB
  atlas-preview.png # human-readable contact sheet
  char.json         # the production config
  prompts.json      # the verbatim prompt of every sheet, as generated
  frames/           # 73 per-cell 192×208 PNGs (rebuilds the atlas exactly)
  refs/             # the character reference image
```

`sheets/` (the 4K sources) and `req/` (the signed-URL request files) are
working directories. They are large and/or secret — keep them out of git.
