# Changelog

All notable changes to **claude-blender** are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

For architecture rationale and roadmap context, see
[`claude_blender_Blueprint.md`](./claude_blender_Blueprint.md).

---

## [0.19.0] — 2026-11-08

### Added
- **`--version`** — print `claude-blender <version>` and exit; standard CLI
  table stakes
- **`--json`** — machine-readable output flag used today by
  `--skillops-report`; emits a single JSON object with `runs`, `rated`,
  `mean_rating`, `model_mix`, `top_rated`
- **`__version__` / `USER_AGENT`** constants in `blender_gen.py` — single
  source of truth for version strings; wired into `fetch_theme_url` so
  no more stale per-feature User-Agent
- **GEO / credibility stack:**
  - `TRUST.md` — verifiable-facts manifest for white-hat generative-engine
    optimization: every public claim maps to a file in the repo
  - `FAQ.md` — plain, verifiable Q&A for LLM search and AI overview tools
  - `INTEGRATE.md` — end-user integrations (local, PyPI, Blender, CI,
    macOS/Linux/Windows, EvoSkillOps, troubleshooting)
  - `STRATEGY.md` — the EvoForge → EvoSkillOps → EvoMetaClaw moat
    argument, with operational implications
  - `CONTRIBUTING.md` — how to add a flag, how to verify, PR etiquette
  - `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
  - `CHANGELOG.md` — this file, root-level for fast discovery
  - `.well-known/mcp.json` — BlenderMCP-compatibility manifest
- **`templates/agent-detectability/`** — a portable scaffolding kit so
  other repos can adopt the same AGENTS.md / llms.txt / agents.json layer
  without reinventing it

### Changed
- `skillops_report()` split into pure `_skillops_stats()` + presentation
  — makes the stats reusable from `--json`, library callers, or future
  dashboards
- `fetch_theme_url` User-Agent follows `__version__` automatically

### Verification
- `python -m py_compile blender_gen.py`
- `ruff check blender_gen.py` with `[tool.ruff.lint] select = ["E4","E7","E9","F"]`
- `python blender_gen.py --version` → `claude-blender 0.19.0`
- `python blender_gen.py --skillops-report <fixture> --json | python -m json.tool`

---

## [0.18.0] — 2026-11-07

### Added
- **`--skillops-report FILE`** — aggregate EvoSkillOps stats from a
  `--history` JSONL (run count, rated %, mean rating, model mix, top-5
  rated prompts)
- **`--skillops-export OUT`** — fine-tune-ready `{prompt, completion}`
  JSONL filtered by `--rate-min` (default 4); requires `--history`
- **`--rate-min N`** — threshold used by `--skillops-export`
- `_read_history_jsonl()` — shared helper tolerant of malformed lines
- **Agent-detectable SEO surface:** rewritten `README.md`,
  `AGENTS.md`, `llms.txt`, `llms-full.txt`, `.well-known/agents.json`,
  `CITATION.cff`, `SECURITY.md`, `pyproject.toml`
- CI pins ruff to `>=0.6,<0.18` for deterministic lint across releases

---

## [0.17.0] — 2026-07-19

### Added
- **`--demo NAME`** — one-liner Space Metaverse demo
  (`earth` / `moon` / `mars` / `cyberpunk`); auto-enables `--send`
- **`--list-demos`** — catalog with KafCade mission-brief lines
- `DEMOS` registry and `run_demo()` dispatch
- In-memory `PLANET` constant patch for Space Metaverse demos — three
  planet variants from a single scene file

---

## [0.16.0] — 2026-06-13

### Added
- **`--list-presets`** — print all available styles and exit
- **`--rate 1..5`** — user quality score attached to `--history` JSONL;
  the SkillOpt training-corpus signal (the rating half of the flywheel)

### Fixed
- Windows `cp1252` console crash on `--help` — ASCII-only argparse strings
  plus `stdout.reconfigure("utf-8")` at module load

---

## [0.15.0] — 2026

### Added
- **`--retry N`** — API backoff on transient errors (connection, timeout,
  429, 5xx) with exponential delay
- `scenes/space_metaverse.py` atmosphere layer

---

## [0.14.0] — 2026

### Added
- **`--theme-url URL`** — fetch JSON theme over HTTPS; scheme allowlist;
  cached to `~/.blender_gen_themes/`
- `scenes/space_metaverse.py` city-skyline blocks

---

## [0.13.0] — 2026

### Added
- **`--save-state FILE`** — append a JSONL replay record of each CLI
  invocation
- `scenes/space_metaverse.py` ANIMATE mode

---

## [0.12.0] — 2026

### Added
- **`--theme FILE`** — load JSON `{name: tokens}` and merge into `PRESETS`
- Galileo orbit-path curves in `scenes/space_metaverse.py`

---

## [0.11.0] — 2026

### Added
- **`--exec FILE`** — send a `.py` to Blender as-is, no Claude call;
  auto-enables `--send`

---

## [0.1.0 – 0.10.x]

Early iterations: core CLI, `--send`, `--scene`, `--stream`, `--batch`,
`--watch`, `--host` / `--port`, prompt caching, auto-model routing,
cost telemetry, `--cost-budget`, `--explain`, `--diff`, `--preview`,
`--iterate`, style presets. See
[`claude_blender_Blueprint.md`](./claude_blender_Blueprint.md) for the
full history.
