# claude-blender Blueprint
**v0.2.0 · 2026-05-29 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)**

---

## Summary
Single-file Python CLI that turns natural language into runnable Blender (`bpy`) scripts via the Claude API.
ARM-native: pure Python, zero native extensions — runs on Apple Silicon, Raspberry Pi, AWS Graviton, x86.

---

## Architecture

```
                  ┌─ --scene ──► Blender MCP socket :9876
                  │                  get_scene_info()
User prompt (CLI) │                       │
        │         │              scene JSON injected into prompt
        ▼         │                       │
  blender_gen.py ◄┘                       ▼
    ├── argparse  →  prompt, model, output, send, scene, stream
    ├── anthropic.Anthropic()
    │    ├── messages.create()        ← default
    │    └── messages.stream()        ← --stream (token-by-token stdout)
    └── bpy script
         ├── stdout / -o FILE         ← default
         └── --send ──► Blender MCP socket :9876
                            execute_code(script)
                                   │
                                   ▼
                            Blender viewport
```

---

## File Manifest

| File | Purpose |
|------|---------|
| `blender_gen.py` | CLI entry point, Claude API call, output |
| `requirements.txt` | `anthropic>=0.57.0` |
| `.gitignore` | excludes .env, __pycache__, venv |
| `CLAUDE.md` | project context for AI coding assistants |
| `claude_blender_Blueprint.md` | this file |
| `claude-blender-prompts.txt` | reference prompts & links |
| `README.md` | GitHub repo landing page |
| `LICENSE` | MIT |
| `.github/workflows/ci.yml` | GitHub Actions CI (lint + syntax, ARM + x86) |

---

## Roadmap

### v0.1 — Shipped ✅
- [x] CLI: `python blender_gen.py "<prompt>"` → stdout
- [x] `--output / -o` flag: write to `.py` file
- [x] `--model` flag: opus / sonnet / haiku
- [x] System prompt engineered for complete, runnable bpy scripts
- [x] ARM-compatible (pure Python)
- [x] GitHub Actions CI: ruff lint + py_compile syntax check (Python 3.10, 3.12 matrix)

### v0.2 — Shipped ✅
- [x] `--send` flag: push script directly to Blender via MCP socket (localhost:9876)
- [x] `--scene` flag: GET live scene state from Blender, inject into Claude prompt
- [x] `--stream` flag: stream Claude output token-by-token to stdout
- [x] Graceful fallback: warns if Blender MCP unreachable; exits 1 only on `--send` fail

### v0.3 — Next 🔲
- [ ] Prompt caching (`cache_control`) on SYSTEM_PROMPT — cut repeat-call cost ~80%
- [ ] Batch mode: `--batch prompts.txt` → generate multiple scripts in one run
- [ ] `--port` flag: configurable MCP socket port (default 9876)
- [ ] `--host` flag: remote Blender support (non-localhost)

---

## API Integrations

| API | Auth | Usage |
|-----|------|-------|
| Anthropic Messages API | `ANTHROPIC_API_KEY` env var | Generate bpy scripts (batch + stream) |
| Blender MCP socket | none (localhost only) | `execute_code`, `get_scene_info` via TCP :9876 |

---

## Changelog

### v0.2.0 — 2026-05-29
- `--send`: execute generated script in live Blender via MCP socket (localhost:9876)
- `--scene`: inject live scene JSON into Claude prompt before generation
- `--stream`: stream Claude response token-by-token to stdout
- All flags composable; graceful error handling on socket failures

### v0.1.1 — 2026-05-29
- Added GitHub Actions CI: ruff lint + py_compile syntax validation (Python 3.10 & 3.12 matrix)
- Merged upstream README.md + LICENSE (MIT) from GitHub initial commit

### v0.1.0 — 2026-05-29
- Initial release: CLI, Claude API integration, ARM-optimized pure-Python implementation
- Models supported: opus-4-7, sonnet-4-6, haiku-4-5

---

*claude-blender Blueprint v0.2.0 · 2026-05-29 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)*
