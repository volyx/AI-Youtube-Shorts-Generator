import json, os, re

t = json.load(open("output/stream2_transcript.json"))
segs = t["segments"]
os.makedirs("output/subs2", exist_ok=True)

clips = [
    (1, 598.0, 636.0),
    (2, 778.0, 808.0),
    (3, 2325.0, 2348.0),
    (4, 1326.0, 1352.0),
    (5, 825.0, 862.0),
]

# context-based spelling fixes
FIXES = [
    (r"код[-\s]?код[ае]?м?", "Claude Code"),
    (r"Код[-\s]?[Кк]од[ае]?м?", "Claude Code"),
    (r"спе[кт][-\s]?дривен", "spec-driven"),
    (r"спек[-\s]?driven", "spec-driven"),
    (r"спект-?", "spec-"),
    (r"[Кк]ликбенч", "ClickBench"),
    (r"опус ", "Opus "),
    (r"стейт[-\s]зе[-\s]арт", "state of the art"),
    (r"Claude Code[а-яё]+", "Claude Code"),   # strip glued Russian case endings
]

def fix(s):
    for pat, rep in FIXES:
        s = re.sub(pat, rep, s)
    return s

def ts(sec):
    if sec < 0: sec = 0
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

MAXC, MAXD = 64, 3.5
def merge(win):
    cues, cur = [], None
    for a, b, txt in win:
        if cur is None:
            cur = [a, b, txt]; continue
        m = (cur[2] + " " + txt).strip()
        if len(m) <= MAXC and (b - cur[0]) <= MAXD:
            cur[1], cur[2] = b, m
        else:
            cues.append(cur); cur = [a, b, txt]
        if cur and cur[2].rstrip().endswith((".", "!", "?")):
            cues.append(cur); cur = None
    if cur: cues.append(cur)
    return cues

for n, start, end in clips:
    win = []
    for s in segs:
        if s["end"] <= start or s["start"] >= end: continue
        txt = (s.get("text") or "").strip()
        if not txt: continue
        a, b = max(0.0, s["start"] - start), min(end, s["end"]) - start
        if b > a: win.append((a, b, txt))
    lines, i = [], 1
    for a, b, txt in merge(win):
        lines += [str(i), f"{ts(a)} --> {ts(b)}", fix(txt), ""]; i += 1
    open(f"output/subs2/clip_{n:02d}.srt", "w", encoding="utf-8").write("\n".join(lines))
    print(f"clip_{n:02d}: {i-1} cues")
