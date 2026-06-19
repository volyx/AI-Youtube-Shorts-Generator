"""Merge transcript segments into ~20s blocks for fast agent scanning."""
import json

T = "/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"
OUT = "/Users/volyx/Movies/2026-05-21 19-12-30/blocks.txt"
BLOCK = 20.0  # seconds per merged block

t = json.load(open(T))
segs = t["segments"]

lines = []
cur_start = None
cur_end = None
buf = []
for s in segs:
    if cur_start is None:
        cur_start = s["start"]
    buf.append(s["text"].strip())
    cur_end = s["end"]
    if cur_end - cur_start >= BLOCK:
        lines.append(f"[{cur_start:7.1f}-{cur_end:7.1f}] " + " ".join(buf))
        cur_start, cur_end, buf = None, None, []
if buf:
    lines.append(f"[{cur_start:7.1f}-{cur_end:7.1f}] " + " ".join(buf))

open(OUT, "w").write("\n".join(lines))
print(f"{len(lines)} blocks -> {OUT}")
