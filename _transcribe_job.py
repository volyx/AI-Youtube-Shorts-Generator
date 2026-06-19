import json, time
from shorts_generator.local.transcriber import transcribe_local, _resolve_backend

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUT = "output/stream2_transcript.json"

t0 = time.time()
print("backend =", _resolve_backend(), flush=True)
transcript = transcribe_local(SRC)
with open(OUT, "w") as f:
    json.dump(transcript, f, ensure_ascii=False)
print(f"DONE in {time.time()-t0:.0f}s | segments={len(transcript['segments'])} "
      f"duration={transcript['duration']:.0f}s -> {OUT}", flush=True)
