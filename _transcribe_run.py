"""Transcribe the source .mov on-device and dump the full transcript JSON.

Run with uv:
    LOCAL_OUTPUT_DIR="/Users/volyx/Movies/2026-05-21 19-12-30" \
        uv run python _transcribe_run.py
"""
import json
import time

from shorts_generator.local.transcriber import transcribe_local

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUT_JSON = "/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"

t0 = time.time()
transcript = transcribe_local(SRC, language=None)
with open(OUT_JSON, "w") as f:
    json.dump(transcript, f, ensure_ascii=False, indent=2)

segs = transcript.get("segments", [])
print(f"DONE in {time.time()-t0:.0f}s — {len(segs)} segments, "
      f"duration={transcript.get('duration', 0):.0f}s -> {OUT_JSON}")
