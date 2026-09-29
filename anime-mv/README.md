# Kutemukan Tuhan di Dirimu — anime-style motion graphics

Part 1 (0:00 – 0:30): `part1_0-30s.mp4` (1920x1080, 30 fps, song audio).

Everything is drawn procedurally in Python (Pillow + numpy) and piped to ffmpeg.
The characters and artwork are original.

## Scenes

| Time | Scene |
| --- | --- |
| 0.0 – 5.1 | Wayang kulit prologue: a gunungan (kayon) shadow rises onto an oil-lamp-lit kelir while the spoken intro is typeset in ink; the kayon spins to close the scene. |
| 5.1 – 5.9 | The camera dives through the kayon's gate, whose doors open onto the next scene. |
| 5.9 – 10.5 | Dusk over a volcano, sawah terraces and coconut palms. The second spoken line is handwritten on screen, then an anime-OP title card slams in, pulsing on the beat (92 BPM). |
| 10.5 – 14.8 | The songwriter's rainy kos room at night, with the Jakarta skyline and Monas outside. The clock races and calendar pages fly from 2023 onward. |
| 14.8 – 19.4 | Close-up of the song sheet. The lyric is handwritten in sync with the vocal while notes fill the staves, beside a rosary and a cup of kopi. |
| 19.4 – 30.0 | Glowing notes drift from his window over kampung genteng roofs and tangled power lines, turn into kamboja petals, and swirl around a hilltop church at dawn before a white-gold bloom. |

## Rendering

```bash
pip install numpy pillow
python3 render.py                    # full render -> out/part1_0-30s.mp4
python3 render.py --stills 3 12 20   # preview frames -> out/still_*.png
```

Word timings for the lyrics live in `timing.py`. They come from faster-whisper word
timestamps, adjusted against the track's loudness envelope.
