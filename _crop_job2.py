import json, time
from shorts_generator.local.clipper import crop_highlights_local
SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
highlights = [
    {"title": "Я не программирую — я генерирую код", "start_time": 598.0, "end_time": 636.0, "score": 92,
     "hook_sentence": "Слово 'программирую' тут лукавое: я уже не настоящий сварщик."},
    {"title": "Забудьте про spec-driven", "start_time": 778.0, "end_time": 808.0, "score": 90,
     "hook_sentence": "Забудьте про spec-driven — там нет 'арт', решают не спеки."},
    {"title": "Зачем библиотека, если можешь сам сделать лучше", "start_time": 2325.0, "end_time": 2348.0, "score": 85,
     "hook_sentence": "Сам Бог велел писать свой тулинг — зачем тебе библиотека?"},
    {"title": "The prompt — единственное, что решает", "start_time": 1326.0, "end_time": 1352.0, "score": 84,
     "hook_sentence": "The prompt — единственный промпт, который реально имеет значение."},
    {"title": "Сколько софта можно переписать", "start_time": 825.0, "end_time": 862.0, "score": 82,
     "hook_sentence": "Представляете, сколько софта можно переписать с Клодом?"},
]
t0 = time.time()
res = crop_highlights_local(SRC, highlights, aspect_ratio="9:16", out_dir="output/shorts2")
json.dump({"source": SRC, "shorts": res}, open("output/result2.json","w"), ensure_ascii=False, indent=2)
print(f"TOTAL {time.time()-t0:.0f}s")
for r in res: print(" ", r.get("clip_url"), r.get("error"))
