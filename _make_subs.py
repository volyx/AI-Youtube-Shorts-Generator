import json, os

t = json.load(open("output/stream_transcript.json"))
segs = t["segments"]

clips = [
    (1, 3560.0, 3624.0),
    (2, 1251.0, 1330.0),
    (3, 2479.0, 2519.0),
    (4, 2566.0, 2606.0),
    (5, 3421.0, 3457.0),
]

os.makedirs("output/subs", exist_ok=True)

def ts(sec):
    if sec < 0: sec = 0
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

MAX_CHARS = 64
MAX_DUR = 3.5

def merge(window):
    """Merge fragmented word-level segments into readable phrase cues."""
    cues, cur = [], None
    for a, b, txt in window:
        if cur is None:
            cur = [a, b, txt]
            continue
        merged = (cur[2] + " " + txt).strip()
        if len(merged) <= MAX_CHARS and (b - cur[0]) <= MAX_DUR:
            cur[1], cur[2] = b, merged
        else:
            cues.append(cur)
            cur = [a, b, txt]
        # flush on sentence-ending punctuation
        if cur and cur[2].rstrip().endswith((".", "!", "?")):
            cues.append(cur)
            cur = None
    if cur:
        cues.append(cur)
    return cues

for n, start, end in clips:
    window = []
    for s in segs:
        if s["end"] <= start or s["start"] >= end:
            continue
        txt = (s.get("text") or "").strip()
        if not txt:
            continue
        a = max(0.0, s["start"] - start)
        b = min(end, s["end"]) - start
        if b > a:
            window.append((a, b, txt))
    lines, idx = [], 1
    for a, b, txt in merge(window):
        lines += [str(idx), f"{ts(a)} --> {ts(b)}", txt, ""]
        idx += 1
    path = f"output/subs/clip_{n:02d}.srt"
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{path}: {idx-1} cues")
