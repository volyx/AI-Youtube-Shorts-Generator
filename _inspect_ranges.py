"""Print raw segments overlapping candidate clip ranges, to pick clean cut points."""
import json

t = json.load(open("/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"))
segs = t["segments"]

RANGES = [
    ("job-fear", 3495, 3550),
    ("benchmark-payoff", 5855, 5910),
    ("spec-driven-bs", 7466, 7520),
    ("claude-human-days", 3100, 3160),
    ("human-bottleneck", 6425, 6495),
    ("openclaw-research", 6045, 6095),
]

for name, a, b in RANGES:
    print(f"\n===== {name}  [{a}-{b}] =====")
    for s in segs:
        if s["end"] >= a and s["start"] <= b:
            print(f"  {s['start']:7.1f}-{s['end']:7.1f}  {s['text'].strip()}")
