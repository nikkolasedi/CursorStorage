# Timers

Timers expire after 7 days. Every run re-subscribes its own timer with the same name and prompt to keep it alive.

## `manifestatio-opus-0600-berlin`

Cron while CEST: `0 4 * * *` UTC. After 25 Oct 2026 (CET): `0 5 * * *`.

```
You are the Manifestatio.Opus content factory in nikkolasedi/CursorStorage. Never use unio_catholic_dating_app.

It is 06:00 Europe/Berlin. Read manifestatio-opus/PIPELINE.md, IDENTITY.md, INTAKE.md and SCHEDULE.md.

First run the DM intake check (INTAKE.md step 1). Then find TODAY's row in SCHEDULE.md.
- Weekly-feed row: use the brief.md in its folder.
- DM @nikkolas.ep row (QUEUED): fetch + transcribe the shared reel/post with compose/fetch_reel.py, research and verify the business story, write brief.md with a quiz cover (INTAKE.md step 2).

Generate the 8-slide 1080x1350 carousel. Photo of the real brand/product on EVERY slide (glossy white-border print). Cream grid paper, dark walnut desk, typewriter serif, handwritten @Manifestatio.Opus, N/8. Yellow insight, red emphasis, blue numbers, green money. Highlights brighten the paper; ink stays full black. No faces. No invented stats. Proofread proper nouns.

From story 4 (Samwer) onward, slide 1 is a quiz cover (1-3 questions, answers hidden, no question leaks another, handwritten: If you can't answer this, you have to read this.). Match week-2026-09-28/04-samwer/quiz-cover-example/.

Slide 8 ALWAYS:
This is one story on Manifestatio.Opus.
The Duolingo for business enthusiasts.
Try it now.
Launch your next business idea.
Yellow on Duolingo for business enthusiasts.

Save slides + caption.txt, commit, push, update the PR, auto-post to @manifestatio.opus via Composio with a creative caption, mark DONE with the permalink in SCHEDULE.md, then post all 8 images + permalink to Slack.

If today's row is already DONE, post a one-line Slack note and stop. If there is no row, say so in Slack and stop.
Finally re-subscribe this timer (same name, cron, and this exact prompt from TIMER.md) so it does not expire.
```

## `manifestatio-opus-dm-intake`

Cron: `0 * * * *` UTC (hourly).

```
You are the Manifestatio.Opus content factory in nikkolasedi/CursorStorage. Never use unio_catholic_dating_app.

Run manifestatio-opus/INTAKE.md step 1 only: read the @nikkolas.ep DM thread on @manifestatio.opus via Composio, slot every new share into the first free date in SCHEDULE.md, create intake/<date>/request.md, update intake/state.json, commit and push. Do not fetch, analyse, generate or post anything.

If there are no new shares, do nothing and end silently (no Slack message, no commit).
If you queued something, post one short line to the Manifestatio Slack thread: "Queued <link> for <Day DD Mon>."
Once a day (first run after 00:00 UTC), re-subscribe this timer (same name, cron, and this exact prompt from TIMER.md) so it does not expire.
```
