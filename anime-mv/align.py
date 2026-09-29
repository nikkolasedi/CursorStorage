"""Aligns the lyric sheet to faster-whisper word timestamps -> lyrics.json.

Each lyric line is (section, text, approx_start, approx_end); words inside a line get
times from matched whisper words, with unmatched words interpolated by length.
"""
import difflib, json, re, sys

LINES = [
 ("intro", "Ketika rasa tidak bisa diungkapkan kata-kata,", 1.30, 4.70),
 ("intro", "Izinkan saya untuk berpuisi", 5.40, 7.60),
 ("v1", "Sudah lama ku menunggu", 11.15, 14.36),
 ("v1", "Sampai selesai kutulis lagu", 15.00, 19.40),
 ("v1", "Lagu yang tak banyak orang dengar", 19.56, 23.76),
 ("v1", "Tapi yang dengar pasti paham maksud perasaanku", 23.76, 29.60),
 ("v2", "\"Sudah siap\" kataku tiga tahun lalu", 30.82, 33.94),
 ("v2", "Tapi perihal waktu Tuhan pasti lebih tahu", 33.94, 36.60),
 ("v2", "Saat itu tak banyak harapan", 36.60, 39.88),
 ("v2", "Tampaknya karena aku terbiasa", 41.64, 46.02),
 ("v2", "Menunggu rusuk yang dulu hilang", 47.04, 48.90),
 ("v2", "Dan tak kunjung datang", 49.48, 51.60),
 ("pre", "Tapi fotomu di gereja itu,", 51.60, 56.80),
 ("pre", "diam diam melintas di eF Ye Pe ku", 56.80, 61.88),
 ("pre", "Gereja yang mungkin hanya aku yang tahu", 61.88, 66.88),
 ("pre", "Pesonamu menghancurkan pesimismeku", 66.88, 71.96),
 ("pre", "Bahwa yang cantik paras dan iman", 71.96, 76.16),
 ("pre", "Masih bisa kutemukan dalam satu insan", 76.16, 83.56),
 ("ch1", "Kata Mama jodoh ada di tangan Tuhan", 85.16, 90.52),
 ("ch1", "Hadirmu di hidupkulah saksinya", 90.52, 95.22),
 ("ch1", "Kalau saja, kamu tidak pindah kerja", 95.22, 100.42),
 ("ch1", "Kalau saja, kamu tidak pindah kota", 100.42, 105.16),
 ("ch1", "Kalau saja, kamu tidak foto di gereja", 105.54, 111.58),
 ("ch1", "Kalau kalau", 111.58, 115.0),
 ("ch1", "Yang perlahan berubah menjadi rasa syukur", 115.0, 124.80),
 ("ch1", "Betapa senang bisa mengenalmu", 125.54, 129.56),
 ("ch1", "Ratusan kecocokan,", 130.54, 134.36),
 ("ch1", "buat ku optimis ini akan mudah dan indah", 134.36, 139.8),
 ("ch1", "Puluhan perbedaan,", 139.8, 144.18),
 ("ch1", "ku yakin kita bisa saling melengkapi", 144.18, 151.98),
 ("v3", "Waktu berjalan, kita pun tumbuh dan saling mengenal", 151.98, 156.4),
 ("v3", "Belajar saling mengerti dan beradaptasi", 156.4, 158.50),
 ("v3", "Doa dipanjatkan guna meyakinkan", 158.50, 160.60),
 ("v3", "Rindu jadi bukti, kamu bukan sekadar pilihan", 161.04, 163.60),
 ("v3", "Restu keluarga perlahan mulai terasa", 163.82, 166.88),
 ("v3", "Tidak hanya sapa, melainkan sudah bertukar doa", 166.88, 172.32),
 ("ch2", "Kata Papa bibit bobot bebet", 172.32, 175.74),
 ("ch2", "Semua ada di dirimu", 175.74, 178.42),
 ("ch2", "Iman dan kasihmu menenangkanku", 178.42, 183.16),
 ("ch2", "Masakanmu enak menyehatkan", 183.16, 188.78),
 ("ch2", "Apalagi yang kucari dan tak kutemukan", 188.78, 193.26),
 ("ch2", "Apalagi yang kutunggu selain kamu", 194.10, 199.86),
 ("outro", "Sisa satu pertanyaanku", 202.40, 206.48),
 ("outro", "Maukah kamu membangun rumah tangga Katolik bersamaku?", 206.48, 216.60),
]

norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
ww = json.load(open(sys.argv[1]))
out = []
for sec, text, ls, le in LINES:
    words = text.split()
    cand = [w for w in ww if w[1] >= ls - 1.0 and w[2] <= le + 1.0]
    sm = difflib.SequenceMatcher(None, [norm(w) for w in words], [norm(c[0]) for c in cand])
    times = [None] * len(words)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            c = cand[blk.b + k]
            times[blk.a + k] = [max(ls, c[1]), min(le, c[2])]
    # fuzzy fill: match remaining words by similarity in order
    for i, w in enumerate(words):
        if times[i] is None:
            best = max(cand, key=lambda c: difflib.SequenceMatcher(None, norm(w), norm(c[0])).ratio(), default=None)
            if best and difflib.SequenceMatcher(None, norm(w), norm(best[0])).ratio() > 0.7:
                prev_end = max([t[1] for t in times[:i] if t] or [ls])
                if best[1] >= prev_end - 0.05:
                    times[i] = [best[1], best[2]]
    # interpolate the rest proportionally to word length
    i = 0
    while i < len(words):
        if times[i] is None:
            j = i
            while j < len(words) and times[j] is None:
                j += 1
            a = times[i - 1][1] if i > 0 else ls
            b = times[j][0] if j < len(words) else le
            if b <= a:
                b = a + 0.25 * (j - i)
            lens = [len(words[k]) + 2 for k in range(i, j)]
            tot = sum(lens); acc = a
            for k, L in zip(range(i, j), lens):
                d = (b - a) * L / tot
                times[k] = [acc, acc + d]; acc += d
            i = j
        else:
            i += 1
    # enforce monotonic starts
    for i in range(1, len(times)):
        if times[i][0] < times[i - 1][0]:
            times[i][0] = times[i - 1][0] + 0.05
        times[i - 1][1] = max(times[i - 1][1], times[i - 1][0] + 0.1)
    times[-1][1] = max(times[-1][1], le)
    out.append({"section": sec, "text": text, "start": times[0][0], "end": le,
                "words": [[w, round(t[0], 2), round(t[1], 2)] for w, t in zip(words, times)]})
json.dump(out, open("lyrics.json", "w"), indent=1, ensure_ascii=False)
for l in out:
    print(f'{l["start"]:7.2f} {l["end"]:7.2f} ' + " ".join(f'{w}@{s}' for w, s, e in l["words"]))
