import json, time
from shorts_generator.local.clipper import crop_highlights_local

SRC = "/Users/volyx/Movies/2026-06-08 19-14-31.mov"

highlights = [
    {
        "title": "OOP was a mistake — and the LLMs finally admit it",
        "start_time": 3560.0, "end_time": 3624.0, "score": 90,
        "hook_sentence": "Во-первых, ООП была ошибкой. И ЛЛМ-ки, слава богу, это наконец поняли.",
        "virality_reason": "Spicy contrarian opinion bomb every developer will argue about, capped with a self-deprecating 'we look like a boss who hasn't coded in 10 years' punchline.",
    },
    {
        "title": "The agent that writes its own skills the more you use it",
        "start_time": 1251.0, "end_time": 1330.0, "score": 88,
        "hook_sentence": "Но чем он отличается? Он самоулучшающийся — он сам создаёт скиллы вокруг ваших запросов.",
        "virality_reason": "Revelation hook: a self-improving agent that learns your patterns and builds its own tools — the core 'wait, what?' idea of the whole stream.",
    },
    {
        "title": "I told the AI my favorite band once — watch what it does",
        "start_time": 2479.0, "end_time": 2519.0, "score": 85,
        "hook_sentence": "Add my favorite band to Apple Notes.",
        "virality_reason": "Live voice-command payoff: the agent recalls 'Blink 182' from yesterday and writes it to Apple Notes — a clean, shareable 'it just works' demo.",
    },
    {
        "title": "Turn your old laptop into a token-printing machine",
        "start_time": 2566.0, "end_time": 2606.0, "score": 84,
        "hook_sentence": "Старый ноутбук будет помирать в кладовке — но генерировать тебе токены.",
        "virality_reason": "Relatable, funny practical hack plus the universal 'after every Apple keynote your laptop is suddenly old' bit — humor + actionable tip.",
    },
    {
        "title": "Every new model needs new skills — and it rewrites them itself",
        "start_time": 3421.0, "end_time": 3457.0, "score": 83,
        "hook_sentence": "Обновился с Опуса 4.7 на 4.8 — и он сам переписывает старые скиллы под новую модель.",
        "virality_reason": "Concrete, forward-looking insight devs will save: skills auto-refactored per model upgrade, a problem people didn't know they had.",
    },
]

t0 = time.time()
shorts = crop_highlights_local(SRC, highlights, aspect_ratio="9:16", out_dir="output/shorts")
result = {"source_video_url": SRC, "highlights": highlights, "shorts": shorts}
with open("output/result.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"DONE in {time.time()-t0:.0f}s")
for i, s in enumerate(shorts, 1):
    print(f"#{i} score={s.get('score')} -> {s.get('clip_url')} err={s.get('error')}")
