# claude-blender Blueprint
**v0.1.0 · 2026-05-29 · [github.com/dnzengou/claude-blender](https://github.com/dnzengou/claude-blender)**

---

## Summary
Single-file Python CLI that turns natural language into runnable Blender (`bpy`) scripts via the Claude API.
ARM-native: pure Python, zero native extensions — runs on Apple Silicon, Raspberry Pi, AWS Graviton, x86.

---

## Architecture

```
User prompt (CLI)
      │
      ▼
blender_gen.py
  ├── argparse  →  prompt, model, output path
  ├── anthropic.Anthropic()
  │       └── messages.create(system=SYSTEM_PROMPT, user=prompt)
  └── stdout / .py file
              │
              ▼
         Blender Text Editor
         (Run Script → bpy executes)
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

---

## Roadmap

### v0.1 — Shipped ✅
- [x] CLI: `python blender_gen.py "<prompt>"` → stdout
- [x] `--output / -o` flag: write to `.py` file
- [x] `--model` flag: opus / sonnet / haiku
- [x] System prompt engineered for complete, runnable bpy scripts
- [x] ARM-compatible (pure Python)

### v0.2 — Next 🔲
- [ ] `--send` flag: push script directly to Blender via MCP socket (port 9876)
- [ ] `--scene` flag: first GET current scene state, include in prompt context
- [ ] Streaming output (stream=True) for long scripts

### v0.3 — Later 🔲
- [ ] Batch mode: read prompts from file, output multiple scripts
- [ ] Prompt caching (cache_control) for repeated SYSTEM_PROMPT calls
- [ ] GitHub Actions CI: lint + dry-run syntax check via `py_compile`

---

## API Integrations

| API | Auth | Usage |
|-----|------|-------|
| Anthropic Messages API | `ANTHROPIC_API_KEY` env var | Generate bpy scripts |

---

## Changelog

### v0.1.0 — 2026-05-29
- Initial release: CLI, Claude API integration, ARM-optimized pure-Python implementation
- Models supported: opus-4-7, sonnet-4-6, haiku-4-5

---

*claude-blender Blueprint v0.1.0 · 2026-05-29*
