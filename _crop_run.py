"""Crop the agent-ranked top 3 highlights to 9:16 into the target folder."""
import json
import time

from shorts_generator.local.clipper import crop_highlights_local

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUT_DIR = "/Users/volyx/Movies/2026-05-21 19-12-30"

highlights = [
    {
        "title": "Why devs trash AI coding: fear of losing their jobs",
        "start_time": 3504.5, "end_time": 3540.1, "score": 92,
        "hook_sentence": "Я задаю себе вопрос: вот этот человек, который это написал — это же я в прошлом.",
        "virality_reason": "Spicy psychoanalysis opinion bomb — claims the real reason developers attack AI coding is fear of losing their jobs and status; built-in agree/disagree debate bait.",
    },
    {
        "title": "I built a database with Claude that's only 3x slower than DuckDB",
        "start_time": 5856.5, "end_time": 5902.5, "score": 90,
        "hook_sentence": "Мы уже приблизились прям очень близко: раньше это было 12 секунд, сейчас 640 миллисекунд.",
        "virality_reason": "Payoff/story peak of the whole build — a hand-rolled analytical DB went from 12s to 183ms and lands within 3x of DuckDB, a concrete jaw-drop result.",
    },
    {
        "title": "Spec-driven development is BS — there's no 'driven' in it",
        "start_time": 7472.2, "end_time": 7514.6, "score": 89,
        "hook_sentence": "Спек-дривен-девелопмент — это какая-то чушь, потому что там нет никакого driven-development.",
        "virality_reason": "Contrarian hot take matching the thumbnail ('forget spec-driven') — calls a trendy methodology nonsense, pure debate bait for the dev crowd.",
    },
]

t0 = time.time()
shorts = crop_highlights_local(SRC, highlights, aspect_ratio="9:16", out_dir=OUT_DIR)
result = {"source_video_url": SRC, "highlights": highlights, "shorts": shorts}
with open(f"{OUT_DIR}/result.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"DONE in {time.time()-t0:.0f}s")
for i, s in enumerate(shorts, 1):
    print(f"#{i} score={s.get('score')} -> {s.get('clip_url')} err={s.get('error')}")
