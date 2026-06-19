"""Print raw segments overlapping candidate clip ranges, to pick clean cut points."""
import json

t = json.load(open("/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"))
segs = t["segments"]

RANGES = [
    ("the-prompt-is-all", 1320, 1372),
    ("write-your-own-tooling", 2288, 2342),
    ("openclaw-agent-setup", 6864, 6914),
    ("caddy-ad", 7282, 7350),
]

for name, a, b in RANGES:
    print(f"\n===== {name}  [{a}-{b}] =====")
    for s in segs:
        if s["end"] >= a and s["start"] <= b:
            print(f"  {s['start']:7.1f}-{s['end']:7.1f}  {s['text'].strip()}")
