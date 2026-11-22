# `char.json` — the production config

One file per pet. It is the single place that describes *what the pet looks
like* and *how the atlas is built*, so the whole thing can be reproduced.

```jsonc
{
  "id": "my-pet",
  "displayName": "My Pet",
  "description": "One line, shown in the app's pet list.",
  "spriteVersionNumber": 2,

  // (1) the character reference request -- a text-only design sheet
  "reference": {
    "output_file": "my-pet-reference",
    "aspect_ratio": "3:4",
    "area": "4K",
    "prompt": "An original chibi anime mascot character design, full body, ..."
  },

  // (2) the prompt blocks shared by every pose sheet
  "prompts": {
    "character": "Picture 1 is the exact character to reproduce in every panel: ...",
    "ground":    "In every panel the character stands on the same horizontal ground line ...",
    "background":"Background: plain seamless pure white in every panel. ...",
    "global_note": ""          // optional, appended to every sheet
  },

  // (3) the sheets, in atlas row order
  "sheet_order": ["idle", "run-right", "run-left", "wave", "jump",
                  "failed", "waiting", "work", "review", "gaze"],
  "sheets": {
    "idle": {
      "aspect_ratio": "3:2",     // the generation canvas shape (see below)
      "cols": 3,
      "rows": 2,
      "frames": 6,               // panels actually used
      "panels": [                // one string per panel
        "Panel 1: front view standing, arms relaxed at her sides, ...",
        "Panel 2: ..."
      ],
      "note": "",                // sheet-wide instruction; omit the key if there is none

      // assembly tuning
      "sheet_file": "sheet-idle-cut.png",
      "clamp_low": 0.90,         // per-frame scale clamp vs the row median
      "clamp_high": 1.10,
      "fixed_scale": false,      // true = every frame in this row gets one scale
      "atlas": { "row": 0 }
    },
    "gaze": {
      "aspect_ratio": "1:1", "cols": 4, "rows": 4, "frames": 16,
      "panels": ["Panel 1: ...", "..."],
      "atlas": { "rows": [9, 10], "columns_per_row": 8 }
    }
  },

  // (4) which sheets go into which generation call
  "batches": {
    "1": ["idle", "run-right", "run-left"],
    "2": ["wave", "jump", "failed"],
    "3": ["waiting", "work", "review"],
    "4": ["gaze"]
  },

  // (5) how frames are normalised into their cells
  "assembly": {
    "target_h": 168,   // median character height inside a 192x208 cell
    "baseline": 196,   // y of the feet inside a cell
    "margin": 4        // keep every sprite this far from the cell edge
  }
}
```

## Per-sheet overrides

A pet is often built over several sessions, and some sheets end up with
slightly different wording. Four blocks may be overridden per sheet:

| Key | Overrides |
|---|---|
| `grid_header` | the "Layout: a sprite sheet of N columns by M rows…" line |
| `character_prompt` | `prompts.character` |
| `ground_prompt` | `prompts.ground` |
| `background_prompt` | `prompts.background` |

The override replaces the value completely — it is not merged.

## `note` is not optional-looking

`"note": ""` and *no* `note` key produce **different prompts**:

* `"note": ""` → the sheet keeps an empty note block, so the prompt has a
  blank paragraph between the panels and the ground line.
* no `note` key → the block is absent entirely.

The generator responds to that whitespace, and the recorded prompts in
`prompts.json` distinguish the two. Keep it faithful when editing.

## `prompts.json` — the record

`prompts.json` holds the **verbatim** prompt of every sheet as it was actually
sent, plus the reference prompt. It is not read by the scripts; it is the
audit trail and the copy-paste source when you need to regenerate exactly one
sheet without touching the rest.

---

## `aspect_ratio` is the generation canvas, not the panel grid

`aspect_ratio` is the shape of the **image the model produces**. It does not
have to equal `cols:rows` — it should be close to it, because a sheet far
from its intended shape gets its panels laid out unevenly.

The aspect that works for each grid in the template:

| Grid | Panels | `aspect_ratio` | Why |
|---|---|---|---|
| 3 × 2 | 6 | `3:2` | exact |
| 4 × 2 | 8 | `2:1` | exact |
| 2 × 2 | 4 | `1:1` | exact |
| 5 × 1 | 5 | `3:1` | wider than 5:1 so the model has room to draw five separate poses without squashing them into one blob |
| 4 × 4 | 16 | `1:1` | exact |

Deviating from these makes the panel splitter work harder and the result less
consistent — not invalid, but not worth it.

---

## Write the reference prompt from a structured brief

The reference prompt is the only thing locking the character identity, and it
is usually the hardest prompt to write because "describe your character" has
too many degrees of freedom. Write the brief down first, then translate it
into prose. A brief that works:

```jsonc
{
  "species": "chick (baby chicken)",
  "silhouette": "single round ball-shaped body, no separate head, no neck, almost as wide as it is tall",
  "proportion_target": "about 1 head tall; the round body IS the character",
  "must_have": [
    "one single round ball body",
    "three small fluffy head feathers on top",
    "two tiny wings folded flat against the sides",
    "two tiny orange three-toed feet"
  ],
  "must_avoid": [
    "no separate head, no neck",
    "no long hair, no ribbons, no glasses, no hat",
    "no spread-out wings in the standing sheets"
  ],
  "palette": { "plumage_main": "#FFD34E", "beak_and_feet": "#F58220" }
}
```

Two things earn their place here:

* **`must_avoid`** — the model happily adds a hat, a ribbon or a second head.
  Listing what must *not* appear is worth as much as listing what must.
* **`silhouette`** — a side-view running pose is the one that breaks the
  cell. Deciding the silhouette in the brief, before any pose sheet exists,
  is what keeps the run row from being scaled down (see `pitfalls.md` #1).
