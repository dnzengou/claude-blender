# claude-blender Blueprint
**v0.4.0 · 2026-05-29 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)**

---

## Summary
Single-file Python CLI that turns natural language into runnable Blender (`bpy`) scripts via the Claude API.
ARM-native: pure Python, zero native extensions — runs on Apple Silicon, Raspberry Pi, AWS Graviton, x86.

---

## Architecture

```
Input modes
  prompt (single)  ──┐
  --batch FILE      ──┤
                      ▼
  blender_gen.py
    ├── --scene ──► MCP get_scene_info()  →  inject JSON into prompt
    ├── SYSTEM_BLOCK  (cache_control: ephemeral — cached after first call)
    ├── anthropic.Anthropic()
    │    ├── messages.create()            ← single / batch
    │    └── messages.stream()            ← --stream
    └── bpy script(s)
         ├── stdout / -o FILE             ← single
         ├── {stem}_{001}.py …            ← --batch --output-dir
         └── --send ──► MCP execute_code()  →  --host HOST --port PORT
                                                  │
                                                  ▼
                                           Blender viewport
                                        (local or remote LAN)
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
| `example_batch.txt` | sample batch prompts file (5 scenes) |
| `prompts/mcp_prompts.md` | Claude Desktop × BlenderMCP prompt library (6 examples) |
| `scenes/cyberpunk_city.py` | reference bpy scene: cyberpunk city grid |
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

### v0.3 — Shipped ✅
- [x] Prompt caching: `cache_control: ephemeral` on SYSTEM_BLOCK — ~80% token cost on repeat hits
- [x] Batch mode: `--batch prompts.txt --output-dir ./scripts/` → `{stem}_{001..n}.py`
- [x] `--host` / `--port` flags: configurable MCP target (local or remote Blender)
- [x] `example_batch.txt`: 5 sample prompts (torus, landscape, city, DNA, solar system)
- [x] `read_batch_prompts()`: skips empty lines and `#` comments

### v0.4 — Shipped ✅
- [x] `--watch FILE`: poll a prompt text file; regenerate + optionally send on each save (hot-reload into Blender)
- [x] `--verbose`: print token usage (input/output + cache hit/write + est. tokens saved) after each call
- [x] `--iterate N`: auto-fix loop — send script to Blender, capture error, re-prompt Claude up to N times

### v0.5 — Next 🔲
- [ ] GUI tray / system-tray launcher (click-to-generate without terminal)
- [ ] `--diff`: show a diff of scene objects before/after execution
- [ ] Named presets: `--preset cyberpunk / nature / abstract` inject style tokens into system prompt

---

## API Integrations

| API | Auth | Usage |
|-----|------|-------|
| Anthropic Messages API | `ANTHROPIC_API_KEY` env var | Generate bpy scripts (batch + stream) |
| Blender MCP socket | none (localhost only) | `execute_code`, `get_scene_info` via TCP :9876 |

---

## Changelog

### v0.4.0 — 2026-05-29
- `--verbose`: token usage after every API call — input, output, cache_hit, cache_write, est_saved tokens
- `--watch FILE`: polling hot-reload (500ms interval) — edit a prompt .txt, save, Blender auto-updates
- `--iterate N`: auto-fix loop — on Blender execution error, Claude repairs the script up to N times
- Removed stale `import os` (unused since v0.1)
- `_send_raw()` extracted; `send_to_blender()` remains backward-compatible

### v0.3.0 — 2026-05-29
- Prompt caching: SYSTEM_PROMPT wrapped in `cache_control: ephemeral` block; ~80% cost reduction on cache hits
- Batch mode: `--batch FILE --output-dir DIR` generates numbered `.py` files, works with `--send`
- `--host` / `--port`: configurable MCP socket target (replaces hardcoded localhost:9876)
- Added `example_batch.txt` with 5 demo prompts

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

*claude-blender Blueprint v0.4.0 · 2026-05-29 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)*
