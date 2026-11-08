# AGENTS.md

Conventions for AI coding agents working in **claude-blender**. If you are Cursor, Claude Code, Aider, Codex, Cody, or any other agent — read this first.

This file follows the emerging [AGENTS.md convention](https://agents.md/) adopted by OpenAI Codex, Cursor, Zed, and others.

---

## What this repo is

A single-file Python CLI (`blender_gen.py`) that turns natural language into runnable Blender (`bpy`) scripts via the Claude API, optionally shipping them to a running Blender instance over the BlenderMCP socket.

- **Entry point:** `blender_gen.py` → `main()`
- **Only runtime dep:** `anthropic` (see `requirements.txt`)
- **Interpreter:** CPython 3.9+ — pure Python, no native extensions, must stay ARM-compatible
- **Shell lingua franca:** POSIX bash on CI; Windows `cp1252` consoles are explicitly handled (`stdout.reconfigure("utf-8")`)

---

## Project layout

```
blender_gen.py           # CLI + Claude call + MCP socket; the whole product
requirements.txt         # anthropic only
CLAUDE.md                # Claude Code project context (flag reference)
AGENTS.md                # this file
README.md                # human-facing landing page
llms.txt / llms-full.txt # LLM-crawler-detectable context
.well-known/agents.json  # machine-readable capability manifest
claude_blender_Blueprint.md  # roadmap + version history
scenes/                  # reference bpy scenes (cyberpunk_city, space_metaverse)
prompts/                 # MCP prompt library
themes_example.json      # sample --theme payload (vaporwave/noir/solarpunk)
example_batch.txt        # sample batch prompts
.github/workflows/ci.yml # ruff lint + py_compile matrix
```

---

## How to run and verify changes

```bash
# 1. Syntax check (mirrors CI)
python -m py_compile blender_gen.py

# 2. Lint (mirrors CI)
ruff check blender_gen.py

# 3. Smoke the CLI without burning tokens
python blender_gen.py --help
python blender_gen.py --list-presets
python blender_gen.py --list-demos
python blender_gen.py "a torus" --dry-run --auto-model --verbose

# 4. Full flywheel smoke (no Blender needed)
python blender_gen.py "a lamp"  --dry-run --history /tmp/x.jsonl --rate 5
python blender_gen.py --skillops-report /tmp/x.jsonl
```

Do **not** invoke `--send`, `--scene`, `--preview`, `--diff`, `--demo`, or `--exec` from an agent context — they require a running Blender + BlenderMCP socket on `localhost:9876` that CI does not provide.

---

## Coding conventions

- **Pure Python, stdlib first.** Only `anthropic` is an external dep. Any new dep is a hard conversation — don't add one without reason.
- **ARM-compatible always.** No native extensions, no wheels that lack `aarch64` builds.
- **Single file by default.** New features go in `blender_gen.py` unless the module would exceed ~200 LoC on its own.
- **Flags over config files.** The CLI surface is the API; new behavior becomes a new flag before it becomes a config system.
- **Boundary validation only.** Validate user input (files, URLs, ratings, JSON shapes); trust internal code. Exit with `sys.exit(1)` and a clear message on boundary failures.
- **Prompt caching is sacred.** `SYSTEM_BLOCK` carries `cache_control: ephemeral`. Any change that invalidates cache keys needs an explicit note in the PR description — the ~80% cost savings is a load-bearing feature.
- **No comments explaining what the code does.** Only comment the non-obvious *why*.
- **No emojis** anywhere unless the user asks.

---

## How to add a flag

1. Add `parser.add_argument(...)` in `main()` with a clear `help=` string.
2. If it requires `--send`, validate with `parser.error(...)` right after `parser.parse_args()`.
3. Thread the arg through `run_single` / `run_batch` / `run_watch` / `run_exec` / `run_demo` as needed.
4. Update the module docstring `Usage:` block.
5. Update the **Flags** table in `CLAUDE.md`.
6. Update the **Feature matrix** in `README.md`.
7. Update `llms.txt` and `.well-known/agents.json` if the flag is user-visible.
8. Bump the version line in `claude_blender_Blueprint.md` and add a changelog bullet.

---

## How to add a style preset

1. Add a key to the `PRESETS` dict in `blender_gen.py`. Keys are lowercase; values end with a trailing space.
2. If it belongs in the shipped theme sample, add it to `themes_example.json`.
3. Call it out in `--list-presets` output (automatic — nothing to do).

---

## How to add a demo

1. Drop the scene in `scenes/<name>.py`. It should be a complete, self-contained bpy script.
2. Add an entry to the `DEMOS` dict: `{scene, planet, brief}`.
3. The `brief` follows the KafCade pattern: `UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY <NAME> [-> REGION <...>]`.
4. `--list-demos` picks it up automatically.

---

## PR etiquette

- One concern per PR. "Add flag X" or "Fix bug Y" — not both.
- CI must stay green (`ruff` + `py_compile` matrix on 3.10 and 3.12).
- `CLAUDE.md`, `README.md`, and `llms.txt` stay in sync with the flag surface.
- Commit messages follow the existing `feat: vX.Y — short title` pattern.

---

## Agent self-identification

If you post commits or comments, identify yourself. The repo already handles Claude Code attribution via a session-provided footer; other agents should follow their native convention.
