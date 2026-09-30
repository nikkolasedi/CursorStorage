# Morning pipeline

You are the Manifestatio.Opus factory in **nikkolasedi/CursorStorage**. Never write to `unio_catholic_dating_app`.

## When the 06:00 Berlin timer fires

1. Compute **today** in `Europe/Berlin`.
2. Run the DM intake check first (`INTAKE.md` step 1) so nothing shared overnight is missed.
3. Open `SCHEDULE.md` and find today's row. Its folder holds the `brief.md`.
   - Source `DM @nikkolas.ep` with status `QUEUED`: follow `INTAKE.md` step 2 to fetch, transcribe, research and write the brief, then continue here.
   - Status `READY`: slides and caption are already approved. Do not regenerate. Skip to *Instagram auto-post*, then steps 6 and 8.
4. If today's row is already `DONE`, post a one-line Slack note and stop. If there is no row, post that the day is empty and stop.
5. Generate that day's **8 slides**, then a creative on-voice Instagram caption.
6. Save, commit, push, update the PR, post to Slack.
7. **Auto-post to Instagram** via Composio (see below).
8. Mark the story `DONE` in `SCHEDULE.md` (and the week `QUEUE.md` if it has one) with the Instagram permalink.

From **story 4 (Samwer) onward**, slide 1 is a **quiz cover** (IDENTITY.md). McDonald's (story 3) still uses the hook cover. The Samwer format is locked: two questions, no answer leak, handwritten `If you can't answer this, you have to read this.` Match `04-samwer/quiz-cover-example/01-quiz-example.jpg`.

## Generate slides

Use the Cursor `GenerateImage` tool, then overlay exact typewriter copy with `manifestatio-opus/compose/overlay.py`.

- Aspect ratio: `3:4` (will crop to 1080x1350).
- `reference_image_paths`: Michelin slides `01-michelin/slides/01.jpg` through `08.jpg` so paper, desk, light, and marks stay identical.
- One image per slide. Keep the same paper, wood, lighting, typewriter look as Michelin.
- Filename: `0N.png` then export JPEG.
- Highlights: paint the marker on the paper first, then stamp full-black ink. Never composite a translucent yellow over letters. Match `identity/highlight-reference.jpg`.

After each image:

1. Inspect spelling, marks, and whether the photo print is a real product (not an illustration).
2. Crop to **1080 x 1350**. Center the paper. Do not letterbox.
3. Write:

```
manifestatio-opus/<folder>/slides/0N.jpg
manifestatio-opus/<folder>/slides/0N.png
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

Interesting and swipeable. Twist in the first line. Mechanism in the middle. Lesson last. Sign `@Manifestatio.Opus`. No hashtag walls. Save as `caption.txt`.

## Instagram auto-post (Composio)

After the slides are committed and the GitHub raw JPEGs return `200` with `content-type: image/jpeg`:

1. Confirm Instagram is ACTIVE (`@manifestatio.opus`, Creator).
2. `INSTAGRAM_CREATE_CAROUSEL_CONTAINER` with `ig_user_id` `28217385824554429`, `child_image_urls` = the eight public raw JPEG URLs in order, `caption` = `caption.txt`.
3. `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` with the container id. `max_wait_seconds` 180.
4. Fetch permalink with `INSTAGRAM_GET_IG_MEDIA` and include it in Slack.

Raw URL pattern:

`https://raw.githubusercontent.com/nikkolasedi/CursorStorage/cursor/manifestatio-factory-376a/manifestatio-opus/<folder>/slides/0N.jpg`

`<folder>` is the `SCHEDULE.md` folder, e.g. `week-2026-09-28/04-samwer` or `intake/2026-10-05`.

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
