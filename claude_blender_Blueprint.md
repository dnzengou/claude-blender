# claude-blender Blueprint
**v0.8.0 · 2026-06-05 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)**

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
| `scenes/space_metaverse.py` | reference bpy scene: geospatial persistent 3D world (Earth/Moon/Mars) |
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

### v0.5 — Shipped ✅
- [x] `--preset STYLE`: inject style tokens before prompt (`cyberpunk` `nature` `abstract` `scifi` `toon`)
- [x] `--diff`: snapshot scene before/after execution, print `+added` / `-removed` object names (requires `--send`)
- [ ] ~~GUI tray launcher~~ — deferred; needs `pystray` (native extension, not ARM-safe)

### v0.6 — Shipped ✅
- [x] `--preview`: sends a 480×270 render script to Blender after execution; opens PNG in system default viewer on localhost; prints path for remote hosts

### v0.7 — Shipped ✅
- [x] `--history FILE`: append `{ts, model, prompt, script}` JSONL record after each generation (single + batch)
- [x] `--auto-model`: heuristic routing — short edits (≤8 words + edit verb) → haiku; long (>20 words) → opus; else `--model` default
- [x] Hardened `--preview`: replaced Windows `subprocess(shell=True)` with `os.startfile` (no shell, safer)

### v0.8 — Shipped ✅ (niche mutation: tool → content)
- [x] `scenes/space_metaverse.py` — geospatial persistent 3D world reference scene; equirectangular lat/lon → world XY (Galileo proxy); procedural terrain (DEM proxy); translucent climate overlay (Copernicus proxy); per-planet config (Earth/Moon/Mars) with deterministic seed; persistent session log at `~/.space_metaverse_state.json` (bounded to last 50 entries); pure bpy + stdlib

### v0.9 — Next 🔲
- [ ] `--cost`: estimate USD spend per call from cached pricing table (input/output/cache token rates)
- [ ] `--dry-run`: print expanded prompt + chosen model without making API call
- [ ] `scenes/space_metaverse.py` extensions: real Copernicus DEM tile fetch (offline cached), real Galileo PRN markers, day/night terminator

---

## Workflow Genome (Evolved · v0.4→v0.7 lineage)

EvoMetaClaw-extracted ESS for shipping a new flag in this project.
Mutate freely; do not splice across boundaries.

```
add_flag(NAME, EFFECT):
  1. module-level constant or helper       (PRESETS dict, RENDER_SCRIPT, EDIT_VERBS)
  2. private _-prefixed helper             (_snapshot, _render_preview, _log_history)
  3. wire into run_single                  (after generation, before/after _send)
  4. wire into run_batch                   (per item, same order)
  5. CLI argparse arg with help string     (verbose mode bonus: print decision)
  6. parser.error guard if depends on flag (e.g. --diff requires --send)
  7. py_compile + ruff check                (gate: 0 errors before commit)
  8. blueprint: shipped ✅ + changelog entry + footer bump
  9. CLAUDE.md flags table + run example   (one-line per flag)
 10. memory: state file flag list + next roadmap
 11. git add SPECIFIC files (not -A)
 12. heredoc commit msg with Co-Authored-By
 13. push origin main
```

**Invariants (broken = circuit breaker):**
- pure Python stdlib only · no native extensions (ARM constraint)
- composable with `--send` / `--batch` / `--watch` (no flag is mutex with these)
- graceful degradation on any socket/file failure (warn + continue, never crash)
- no hardcoded secrets · `ANTHROPIC_API_KEY` is the only auth surface
- `shell=True` forbidden when stdlib has a native API (e.g. `os.startfile`)

**Mutation history:**
| Epoch | Diversity injected | Trigger |
|-------|-------------------|---------|
| v0.5 | `--preset` + `--diff` | Circuit breaker: GUI tray rejected (pystray = native) |
| v0.6 | `--preview` | Visual feedback gap detected post-v0.5 |
| v0.7 | `--auto-model` + security harden | Cost-optimisation + grep audit finding |
| v0.8 | `scenes/space_metaverse.py` (**niche jump**: CLI flag → content asset) | EvoMetaClaw signal from external script: bridge geospatial + persistent + 3D world |

---

## API Integrations

| API | Auth | Usage |
|-----|------|-------|
| Anthropic Messages API | `ANTHROPIC_API_KEY` env var | Generate bpy scripts (batch + stream) |
| Blender MCP socket | none (localhost only) | `execute_code`, `get_scene_info` via TCP :9876 |

---

## Changelog

### v0.8.0 — 2026-06-05
- `scenes/space_metaverse.py` (~150 LOC, pure bpy + stdlib) — implements the "Bridging Space Data & Gaming Innovation" deck as a runnable reference scene:
  - **Geospatial backbone**: equirectangular `latlon_to_xy()` projection (Galileo GNSS proxy)
  - **Persistent world**: JSON session log at `~/.space_metaverse_state.json` with bounded history (last 50)
  - **3D immersive**: subdivided plane terrain with deterministic procedural displacement (DEM proxy), translucent emissive climate overlay (Copernicus proxy), sun light, framed camera
  - **Multi-planet**: `PLANET = "earth" | "moon" | "mars"` switch; per-planet color/seed/sun-energy/amplitude
  - **6 Galileo markers**: Equator-Null, Paris, Tokyo, Rio, Sydney, McMurdo
  - **Render engine auto-detect**: Eevee Next on 4.2+, fallback to Eevee
- Niche jump: project mutates from CLI-flag niche (v0.4→v0.7) to content-asset niche (v0.8); Workflow Genome recipe still applies (steps 1-2,7-13)
- Blueprint mutation history table extended; v0.9 roadmap seeded with both CLI cost flags and space scene extensions

### v0.7.1 — 2026-06-04
- Docs: added **Workflow Genome** section — EvoMetaClaw-extracted ESS pattern from v0.4→v0.7 lineage; 13-step recipe for adding a new flag; invariants list (ARM/composability/graceful degradation/no shell=True/no hardcoded secrets); mutation history table with circuit-breaker triggers
- No code changes; reduces re-derivation cost for future contributors and future Claude sessions

### v0.7.0 — 2026-06-03
- `--history FILE`: append-mode JSONL log; one record per generation with UTC isoformat timestamp, model, expanded prompt, output script; survives parallel processes
- `--auto-model`: word-count + verb-prefix heuristic; short edit verbs route to haiku for speed, long descriptions route to opus for quality, neutral prompts honour `--model`
- Security hardening: Windows preview opener now uses `os.startfile` (stdlib) — eliminates `shell=True`; ARM/Linux/macOS paths unchanged
- `EDIT_VERBS` constant: 13 verbs covering common edit intents (add/remove/move/scale/rotate/...)
- Verified routing live: "add a red cube" → haiku, "spinning torus" → default, 20+ word scene → opus

### v0.6.0 — 2026-06-01
- `--preview`: after `--send`, sends a bpy render script (480×270 PNG, auto-camera if none) to Blender via MCP socket; opens result in system default viewer on localhost (`open`/`xdg-open`/`start`); prints path only for remote hosts; degrades gracefully on any socket or render failure
- Pure Python: `subprocess` + `platform` (stdlib) — zero native extensions, ARM-safe
- `_render_preview()` + `_open_preview()` extracted as standalone helpers; wired into both `run_single` and `run_batch`

### v0.5.0 — 2026-05-30
- `--preset STYLE`: 5 built-in style presets (`cyberpunk`, `nature`, `abstract`, `scifi`, `toon`) — each injects a style token string before the user prompt; pure Python dict, ARM-safe
- `--diff`: snapshots scene via `get_scene_info` before and after execution; diffs object name sets; prints `+added`/`-removed` counts; requires `--send`; gracefully degrades on socket failure
- GUI tray deferred — `pystray` uses native OS extensions, breaks ARM compatibility
- `_snapshot()` helper extracted for clean before/after scene capture

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

*claude-blender Blueprint v0.8.0 · 2026-06-05 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)*
