"""Word-level timings for the first 30 seconds (seconds from song start).

Derived from faster-whisper word timestamps, corrected against the RMS
envelope of the track (whisper places the first word of each phrase too early).
"""

INTRO_1 = [
    ("Ketika", 1.30, 2.24), ("rasa", 2.24, 2.52), ("tidak", 2.52, 2.84),
    ("bisa", 2.84, 3.12), ("diungkapkan", 3.12, 4.04), ("kata-kata,", 4.04, 4.70),
]
INTRO_2 = [
    ("Izinkan", 5.40, 6.40), ("saya", 6.40, 6.66), ("untuk", 6.66, 6.86),
    ("berpuisi", 6.86, 7.60),
]
V1_L1 = [("Sudah", 11.15, 11.80), ("lama", 11.80, 12.14), ("ku", 12.14, 12.58),
         ("menunggu", 12.58, 14.36)]
V1_L2 = [("Sampai", 15.00, 16.38), ("selesai", 16.38, 17.24), ("kutulis", 17.24, 18.22),
         ("lagu", 18.22, 19.40)]
V1_L3 = [("Lagu", 19.56, 21.04), ("yang", 21.04, 21.38), ("tak", 21.38, 21.74),
         ("banyak", 21.74, 22.14), ("orang", 22.14, 22.76), ("dengar", 22.76, 23.76)]
V1_L4a = [("Tapi", 23.76, 24.20), ("yang", 24.20, 24.68), ("dengar", 24.68, 25.98),
          ("pasti", 25.98, 26.58), ("paham", 26.58, 27.32)]
V1_L4b = [("maksud", 27.32, 27.72), ("perasaanku", 27.72, 29.60)]

BPM = 92.3
BEAT = 60.0 / BPM
