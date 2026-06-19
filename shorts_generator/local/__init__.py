"""Local-mode backends — no MuAPI calls, runs on your machine.

Used when the pipeline is invoked with mode="local". Requires the `local`
dependency group (yt-dlp, mlx-whisper/faster-whisper, opencv) installed via
`uv sync`; cloud LLM ranking additionally needs the `cloud-llm` group.
"""
