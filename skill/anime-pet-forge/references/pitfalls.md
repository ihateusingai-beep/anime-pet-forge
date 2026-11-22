# Pitfalls

Every one of these was hit for real while building the three pets in this
repository. Each of them fails **quietly** — the validator passes, the import
succeeds, and the pet is simply wrong.

---

## 1. A character that overflows its cell gets silently shrunk

The cell is 192 px wide. A cat with a streaming tail is 1.4× wider than it is
tall, so the assembler has to scale the whole run row down to fit — and the
cat in the run animation suddenly appears smaller than the cat everywhere
else. Nothing warns you. The validator sees a legal atlas.

**Fix:** constrain the silhouette *in the prompt*, then regenerate the sheet:

> "the fluffy tail is curled UP over the back in a compact curve close to the
> body, never stretched out behind. The whole cat stays compact: the total
> width of the cat is only slightly wider than the cat is tall."

The assembler prints a `cap=` value per row. `cap=1.00` means no row was
shrunk to fit. Anything below 1.00 is a row that got smaller than it should
be.

## 2. Long hair fans out unless you tell it not to

"long straight hair" alone gives you a character 250 px wide. Add a global
note to every sheet:

> "Her long hair hangs in a compact curtain close to her body in every pose,
> never fanning out to the sides."

`prompts.global_note` is the place for this — it is appended to every sheet.

## 3. Long hair also has to stream *correctly* while running

The same hair that hangs in a neat curtain while idle has to stream backward
while running. Say both, per sheet:

> "her long hair hangs in a compact curtain close to her back and shoulders,
> never fanning out wide. The whole figure stays upright and narrow: the
> total width of the character is only slightly wider than she is tall."

## 4. The model cannot be trusted to draw 16 distinct gaze directions

Ask for 16 panels and it will give you 16 nearly identical heads with a
little eye movement. The spec demands real head rotation: up, up-right,
right, right-down, down, down-left, left, left-up, in 22.5° steps.

Make it explicit that the **body does not move** and only the head turns:

> "In all sixteen panels the character's whole body is in exactly the same
> position … ONLY the head and the eyes change direction from panel to panel,
> turning on the neck. The body is a copy of the body in panel 1 in every
> panel."

Even then, check up / right / down / left by eye. Sixteen different hashes
prove nothing.

## 5. Sheet panels are not evenly sized

The model does not lay out a 4×4 grid of equal panels. The assembler finds
the real boundaries from the alpha mask, so uneven panels are survivable —
but only if the column detector works. It breaks when the sheet contains a
**faint full-width line** (a horizon, a table edge). The threshold is
relative (2 % of the peak), so a soft horizon reads as content and the
column count stops matching.

**Fix:** pure white background, no ground line, no horizon, no shadow.

## 6. The reference URL expires

The reference image is uploaded to a signed temporary URL, typically valid for
about an hour. After that the generation call fails — or worse, succeeds with
a *different* character, because the model treats the missing reference as a
blank slate.

**Fix:** re-upload the reference before **every** batch.

## 7. `req/*.json` contains credentials

The request files embed the signed reference URL, including
`x-oss-credential`, `x-oss-signature` and an expiry timestamp. The signature
is short-lived, but the credential id is not a secret to leave lying around
in a public repo.

**Fix:** keep `req/` out of git. The prompts themselves live in
`prompts.json`, which is safe.

## 8. An empty note block is not the same as no note block

`"note": ""` keeps an empty paragraph in the prompt; omitting the key removes
the paragraph. The generator reads that whitespace differently, and the
recorded prompts distinguish the two. When migrating an existing pet, keep
the difference — see `references/character-config.md`.

## 9. Import can look like it failed when it succeeded

After the app reads the files it clears the file input, so any tool that
inspects the input afterwards sees zero selected files and reports a
mismatch. Read the app's own result panel instead of the input state.

## 10. The import panel hides inside the desktop overlay window

When the desktop pet window is open, the app's main panel is
`display:none !important`, and the import view is a child of that panel.
Make it visible, open the import view, upload, confirm — then put the
overlay back the way you found it, or the floating window goes white.

## 11. The validator does not judge art

It checks metadata, PNG encoding, dimensions, non-empty cells and transparent
backgrounds. It cannot see that the character changed between frames, that
the run cycle does not loop, or that the gaze is pointing the wrong way.

Open the atlas and look at it. A contact sheet of every row is the fastest
way to spot a broken row.

## 12. A v1 pet is not a v2 pet with blank rows

If the sixteen look poses cannot be made, ship **v1**: 1536 × 1872, 8 × 9,
`spriteVersionNumber: 1`. Two empty rows do not make a v2 pet, and the
validator will notice the empty cells.
