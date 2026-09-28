# Morning pipeline

You are the Manifestatio.Opus factory in **nikkolasedi/CursorStorage**. Never write to `unio_catholic_dating_app`.

## When the 06:00 Berlin timer fires

1. Compute **today** in `Europe/Berlin`.
2. Open `week-2026-09-28/QUEUE.md` and the matching `brief.md`.
3. If today's row is already `DONE`, post a one-line Slack note and stop.
4. If today is before Tue 29 Sep 2026 06:00 Berlin, **do not generate**. Wait.
5. Generate that day's **8 slides**, then the 4-sentence caption.
6. Save, commit, push, update the PR, post to Slack.
7. Mark the story `DONE` in `QUEUE.md`.

Tuesday 29 Sep is **IKEA**. Generate IKEA first.

## Generate slides

Use the Cursor `GenerateImage` tool.

- Aspect ratio: `3:4` (will crop to 1080x1350).
- `reference_image_paths`: Michelin slides `01-michelin/slides/01.jpg` through `08.jpg` so paper, desk, light, and marks stay identical.
- One image per slide. Keep the same paper, wood, lighting, typewriter look as Michelin.
- Filename: `0N.png` then export JPEG.

After each image:

1. Inspect spelling, marks, and whether the photo print is a real product (not an illustration).
2. Crop to **1080 x 1350**. Center the paper. Do not letterbox.
3. Write:

```
manifestatio-opus/week-2026-09-28/<story>/slides/0N.jpg
manifestatio-opus/week-2026-09-28/<story>/slides/0N.png
```

If a mark landed on the wrong words, or a face appeared, or a number was invented, regenerate that slide. Do not invent stats. If a figure is not in the brief, drop it.

Copy finals to `/opt/cursor/artifacts/manifestatio-<story>-0N.jpg` so Slack can render `<img>` tags.

## Slide 8 lock

Always this text, spelled correctly:

```
This is one story on Manifestatio.Opus.
The Duolingo for business enthusiasts.
Try it now.
Launch your next business idea.
```

Yellow on **Duolingo for business enthusiasts**. Blue arrow to the last line. Handwritten `link in bio`. Small product photo print still on the sheet.

## Caption

Four sentences. Company in sentence 1. Mechanism in the middle. Lesson last. Sign `@Manifestatio.Opus`. Save as `caption.txt`.

## Git

Branch: stay on `cursor/manifestatio-factory-376a` (or the current factory branch).

```
git add manifestatio-opus
git commit -m "Add <story> 1080x1350 carousel slides"
git push -u origin HEAD
```

Update the existing PR. Do not open a dating-app PR.

## Slack

Post in the existing Manifestatio thread:

1. Short recap + the 4-sentence caption.
2. All 8 images as `<img alt="slide N/8" src="/opt/cursor/artifacts/manifestatio-<story>-0N.jpg" />`.
3. GitHub links to the committed JPEGs.

Do not ask the user to wait between slides in the 6am run. Generate all 8, then post.

## Hard rules

- No faces.
- No extra text beyond the brief.
- Photo of the real brand/product on **every** slide (glossy white-border print).
- Yellow = insight, red = emphasis, blue = numbers/action, green = money/growth.
- Extra research is allowed only to make the brief more precise. Never invent a number. Never use a forbidden claim from the brief.
