# DM intake

`@nikkolas.ep` shares a reel or post with `@manifestatio.opus`. It becomes a scheduled Manifestatio carousel.

Only messages from `@nikkolas.ep` created after `accept_after` in `intake/state.json` count. Ignore every other sender and everything older.

## 1. Slot it (hourly intake timer)

1. Composio `INSTAGRAM_LIST_ALL_MESSAGES` on `conversation_id` from `intake/state.json`, fields `id,from,created_time,message,shares,attachments`. Rows are under `data.data`.
2. Keep messages where `from.username == "nikkolas.ep"`, `created_time > accept_after`, and `id` is not in `processed_message_ids`.
3. If `next_share_is_test` is `true` in `intake/state.json`, the first new share is a **test run**: build it into `intake/test-run/` (step 2, no Instagram upload, no `SCHEDULE.md` row), mark it processed, set `next_share_is_test` to `false`, and report the slides to Nikkolas. Later shares follow the normal flow.
4. For each, oldest first:
   - Link = `shares.data[0].link`, or a URL in `message`, or `attachments` media URL.
   - Plain text without a link is a note for the share right before or after it (within 10 minutes). Otherwise skip it.
   - Slot = first date after today (Berlin) with no row in `SCHEDULE.md`.
   - Create `intake/<YYYY-MM-DD>/request.md` with link, note, sender, `created_time`, message id.
   - Add a `SCHEDULE.md` row: date, `TBD (DM)`, `DM @nikkolas.ep`, `intake/<YYYY-MM-DD>`, `QUEUED`.
   - Append the message id to `processed_message_ids`.
5. Commit and push (`Queue DM share for <date>`). Do not analyse yet.
6. If within 24h of the message, reply via `INSTAGRAM_SEND_TEXT_MESSAGE`: `Queued for <Day DD Mon>.` If it fails, skip it silently.

Never log `paging.next`. It contains an access token.

## 2. Build it (06:00 run on the slot date)

1. `pip install -q yt-dlp faster-whisper` if missing.
2. `python3 manifestatio-opus/compose/fetch_reel.py <link> manifestatio-opus/intake/<date>/raw`
   - Writes `source.json` (creator, caption), `video.mp4`, `transcript.txt`, `frames/`.
   - If the fetch fails (private account, rate limit), use the caption from the DM preview plus the note. If that is not enough, pick the next PENDING weekly story instead and tell Slack.
3. Read transcript, caption and frames. Identify the **business story**: company, founder, mechanism, twist, numbers.
4. Research to verify every fact and number. Drop anything you cannot confirm. Never copy the reel's wording or visuals. Retell the story in Manifestatio voice.
5. Write `intake/<date>/brief.md` in the same shape as `week-2026-09-28/04-samwer/brief.md`: quiz cover (slide 1), slides 2–7, locked slide 8, photo-print subject per slide, marks, sources.
6. Update the `SCHEDULE.md` row with the story name.
7. Continue with `PIPELINE.md` from *Generate slides*. Output goes to `intake/<date>/slides/` and `intake/<date>/caption.txt`.
8. Credit the original creator in the caption only if the story is theirs (interview, original reporting): `Story via @<creator>`.

Do not commit `raw/video.mp4` or `raw/frames/`. They are listed in `.gitignore`.
