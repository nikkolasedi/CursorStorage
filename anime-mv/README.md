# Kutemukan Tuhan di Dirimu — anime-style motion graphics

- Full song (3:41): `kutemukan_tuhan_full.mp4` (1920x1080, 30 fps)
- First 30 seconds only: `part1_0-30s.mp4`

Everything is drawn procedurally in Python (Pillow + numpy + scipy) and piped to ffmpeg.
All characters (the songwriter, the girl, Mama, Papa and both families) are original chibi designs in `cast.py`.

## Scenes

| Time | Section | Style / idea |
| --- | --- | --- |
| 0:00 | Intro | Wayang kulit shadow screen; the gunungan spins, then its gate opens onto a dusk volcano and the title card |
| 0:10 | Verse 1 | Rainy kos room with Monas outside, the song handwritten on paper, notes flying over kampung roofs to a church |
| 0:30 | Verse 2 | Sepia VHS flashback "SUDAH SIAP!" (2023), then God's hourglass descends |
| 0:36 | | Grey ink-wash halte in the rain, an angkot splashes past; the only colour is his yellow umbrella |
| 0:41 | | Routine grid with a day counter rolling up to day 1,095 (three years) |
| 0:47 | | Stained-glass (kaca patri) window: the rib lifts away and leaves an empty heart |
| 0:51 | Pre-Chorus | Phone feed scrolling kucing oren, nasi goreng and macet, then stopping on her church photo; double-tap hearts and F / Y / P stickers |
| 1:02 | | Paper map of Indonesia; a pin drops on a church "cuma aku yang tahu" |
| 1:07 | | "PESIMIS" cracks and shatters into glass shards, and "PESONA" blooms |
| 1:12 | | Cirebon mega mendung batik portrait: the flower for *paras* and the cross for *iman* merge into one heart |
| 1:25 | Chorus 1 | Mama in kebaya: "jodoh di tangan Tuhan"; the camera tilts up to God's hands holding a red thread |
| 1:35 | | Black-and-white manga panels: pindah kerja, a train to another city, "CKREK!" church photo |
| 1:51 | | "KALAU..." manga SFX echo, with shaking and inverting panels |
| 1:55 | | The grey panels turn into colourful sky lanterns over a lake: gratitude |
| 2:05 | | Pop-art sunburst joy with red-and-white confetti |
| 2:10 | | Compatibility meter reaching 100% "MATCH!" with shared-interest tags |
| 2:20 | | Differences (bubur diaduk vs tidak diaduk...) then parang and mega-mendung puzzle halves lock into a heart |
| 2:32 | Verse 3 | Scooter ride through the sawah as roadside posts count the years; rain, one shared jas hujan |
| 2:38 | | Votive candles lit one by one |
| 2:41 | | Split-screen video call under the same moon |
| 2:44 | | Two families at a nasi tumpeng dinner, then prayers in the "Keluarga Besar" group chat |
| 2:52 | Chorus 2 | Papa's pixel-RPG status screen: BIBIT / BOBOT / BEBET MAX, "LULUS!" |
| 2:58 | | Calm lake at dawn, the couple in a wooden boat |
| 3:03 | | Top-down wajan cooking: "ENAK!", "+100 HP", "SEHAT!" |
| 3:09 | | Search engine: "apa lagi yang kucari?" returns one result, "Kamu" |
| 3:14 | | The waiting clock finally stops: "TING!" |
| 3:20 | Outro | Golden-hour proposal outside the church, with letterbox bars and a ring box |
| 3:26 | | Blueprint of a joglo house drawn line by line; the cross lights up and the plan fills with colour |
| 3:36 | | Fireworks and a "Maukah kamu?" card with two buttons, both saying yes |

## Rendering

```bash
pip install numpy pillow scipy
python3 full.py                        # whole song -> out/full.mp4
python3 full.py --stills 40 100 200    # preview frames -> out/full_*.png
python3 full.py --start 95 --end 116   # re-render one section
python3 render.py                      # original 30 s cut
```

- `lyrics.json` holds per-word timings. `align.py` rebuilds it from faster-whisper word timestamps.
- The scene timeline, transitions and lyric styles live at the top of `full.py`.
