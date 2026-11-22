# MiniMax Pet v2 atlas — the numbers you need

Condensed from the official `minimax-pet` skill's `references/spritesheet-format.md`.
Read the official file for the full contract; this is the working summary.

## Deliverable

```text
my-pet/
  pet.json
  spritesheet.png
```

| Field | Rule |
|---|---|
| `id` | 1–80 chars, `^[a-z0-9][a-z0-9._-]{0,79}$`. New custom id; `minimax-original` is reserved. `minimax-pet` is the plugin identity — never change it. |
| `displayName` | nonblank, no leading/trailing spaces, ≤ 80 UTF-16 code units |
| `description` | optional, ≤ 300 UTF-16 code units, not `null` |
| `spritesheetPath` | same-directory plain filename, `^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.(webp\|png)$`, lowercase extension matching the real encoding |
| `spriteVersionNumber` | `1` or `2` — a number, not the string `"2"` |

Do **not** add `agentAccess` or any author/license/animation field. Keep
attribution in the repo, not in the metadata.

## Canvas

| Version | Size | Grid | Content |
|---|---|---|---|
| v1 | 1536 × 1872 | 8 × 9 | 9 animation tracks |
| **v2** | **1536 × 2288** | **8 × 11** | 9 tracks + 16 look poses |

Cell = **192 × 208**. Cell `(col, row)` starts at `(col*192, row*208)`.
No gutters, no margins, no labels, no grid lines. Unused trailing cells stay
fully transparent.

Encoding profile: **static 8-bit RGBA, non-interlaced PNG**, real alpha, and
the alpha must actually be transparent — no baked white, no checkerboard, no
pedestal, no caption. GIF, APNG, video, JPEG, SVG and a single portrait are
not an atlas.

## The nine animation rows

| Row | Track | Frames | Columns |
|---|---|---|---|
| 0 | `idle` | 6 | 0–5 |
| 1 | `running-right` | 8 | 0–7 |
| 2 | `running-left` | 8 | 0–7 |
| 3 | `waving` | 4 | 0–3 |
| 4 | `jumping` | 5 | 0–4 |
| 5 | `failed` | 8 | 0–7 |
| 6 | `waiting` | 6 | 0–5 |
| 7 | `running` (working) | 6 | 0–5 |
| 8 | `review` | 6 | 0–5 |

57 animation cells. Keep identity, palette, scale and foot baseline
consistent; keep every limb inside its cell; make the motion connect across
the cycle. Row 7 is *working*, not a second right-run.

## The two look rows (v2 only)

Zero degrees points **UP**, increasing clockwise in **22.5°** steps. It does
not start facing right.

| Row | Columns |
|---|---|
| 9 | 0 up · 22.5 up/right · 45 up-right · 67.5 right/up · 90 right · 112.5 right/down · 135 down-right · 157.5 down/right |
| 10 | 180 down · 202.5 down/left · 225 down-left · 247.5 left/down · 270 left · 292.5 left/up · 315 up-left · 337.5 up/left |

Index `i` → row `9 + floor(i/8)`, column `i % 8`. 73 valid cells total.

Sixteen different hashes do not prove correct direction. Look at up / right /
down / left yourself.

## Size and validation boundaries

* The **image** budget is 8 MiB. The **HTTP request** limit is 12 MiB for the
  whole UTF-8 JSON, because base64 expands the image by ~4/3:
  `ceil(imageBytes / 3) * 4 + 4096 <= 12 * 1024 * 1024`.
* The official validator checks metadata, **PNG** decoding, dimensions,
  non-empty cells and transparent backgrounds. Edge contact, motionless tracks
  and repeated gaze cells produce **warnings**. It does **not** decode WebP —
  the runtime can import static WebP, but `validate-art.mjs` only proves
  things about the PNG profile. If you ship a WebP, the validator's "ok" says
  nothing about it.
* It reads no Host state, changes no import state, cannot see whether an id
  already exists, and cannot understand the character or the action meaning.

## Timeline

Playback timing belongs to the player, not to the JSON. Idle's six frames
total 6600 ms. Non-idle actions play three cycles and return to slow idle.
Do not add frames or GIF delays to change timing.
