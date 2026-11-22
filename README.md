# claude-blender

**Natural language → Blender Python scripts, powered by Claude.** One CLI. Zero plugins. Any machine, any CPU.

**v0.21** — Gemini provider · 17-test unit suite · GitHub Pages auto-deploy · `--open` launches the local UI.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows%20%7C%20arm64-lightgrey)
![claude](https://img.shields.io/badge/claude-opus%204.7%20%7C%20sonnet%204.6%20%7C%20haiku%204.5-5A3FFF)
![license](https://img.shields.io/badge/license-MIT-green)
![agent-ready](https://img.shields.io/badge/agent--ready-AGENTS.md%20%E2%80%A2%20llms.txt-black)

> **One line in. One scene out.**
> `python blender_gen.py "a spinning gold torus"` ships runnable `bpy` code to Blender over MCP in seconds.

---

## Why claude-blender

Pair Claude's coding intelligence with Blender's 3D engine and treat prompts as a *technical director*. The CLI is the glue: it talks to Claude for code, to Blender for execution, and to your flywheel for everything that comes next.

- **Multi-provider.** Anthropic Claude, DeepSeek, or Google Gemini — flip with `--provider`, same prompts, same quality signal.
- **Runs in the browser.** Single static HTML in `web/` — no server, no build, no deps. Open the file, paste a key, generate.
- **Pure Python.** No native extensions. Runs on Apple Silicon, Raspberry Pi, AWS Graviton, x86.
- **Prompt-cached system block.** ~80% token-cost reduction after the first call in a batch.
- **Live scene round-trip.** `--scene` pulls the current Blender state back into the prompt; `--send` pushes the generated script back into the viewport.
- **Space Metaverse ready.** Built-in `--demo earth|moon|mars|cyberpunk` ships a geospatial 3D world in one command — Galileo markers, orbit curves, Copernicus climate overlay.
- **Commercial surface.** Theme packs, cost budgets, replay logs, EvoSkillOps flywheel — the plumbing you need to productize an AI design loop.
- **Agent-detectable.** Ships `AGENTS.md`, `llms.txt`, `llms-full.txt`, and `.well-known/agents.json` so coding agents and LLM crawlers discover and self-orient here without hand-holding.

---

## 60-second Quickstart

```bash
# 1. Install
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...     # https://console.anthropic.com/

# 2. Verify — one command, zero tokens
python blender_gen.py --doctor

# 3. First scene — no Blender needed, no tokens burned
python blender_gen.py "a spinning gold torus" --dry-run --auto-model

# 4. Real scene — prints runnable bpy code to stdout
python blender_gen.py "a spinning gold torus on a marble pedestal"

# 5. Ship it to Blender (needs BlenderMCP add-on + 'Connect to Claude' pressed)
python blender_gen.py "add neon lights to the scene" --scene --send

# 6. One-liner value demo — a geospatial Earth scene end-to-end
python blender_gen.py --demo earth --preview
```

Stuck? `python blender_gen.py --doctor` tells you which step is red.

### Prefer the browser?

```bash
# Local — open the file. No server needed.
open web/index.html          # macOS
xdg-open web/index.html      # Linux
start web\\index.html        # Windows
```

Paste an Anthropic or DeepSeek key once (stored in your browser only), pick a model, press <kbd>Ctrl</kbd>+<kbd>Enter</kbd>. Copy or download the `.py` and paste into Blender's Text Editor. Host it on GitHub Pages if you want a zero-backend SaaS surface.

### Pick a provider

```bash
# Default: Anthropic
python blender_gen.py "spinning torus"                         # opus-4-7

# Switch to DeepSeek (OpenAI-compatible, no new dep)
export DEEPSEEK_API_KEY=sk-...
python blender_gen.py "spinning torus" --provider deepseek     # deepseek-chat

# Switch to Google Gemini (OpenAI-compatible, no new dep)
export GEMINI_API_KEY=...
python blender_gen.py "spinning torus" --provider gemini       # gemini-2.5-flash

python blender_gen.py --list-models                            # full catalog
python blender_gen.py --open                                   # launch the browser UI
```

---

## Feature matrix

| Capability | Flag | What you get |
|---|---|---|
| Live execution | `--send` | Push script to running Blender via MCP socket |
| Scene round-trip | `--scene` | Inject live Blender state into the prompt |
| Streaming | `--stream` | Token-by-token stdout streaming |
| Batch | `--batch FILE` | One script per prompt line |
| Hot-reload | `--watch FILE` | Regenerate + send on every save |
| Run as-is | `--exec FILE` | Ship a `.py` to Blender with no Claude call |
| Auto-fix loop | `--iterate N` | Re-prompt Claude on Blender error up to N times |
| Style presets | `--preset STYLE` | cyberpunk · nature · abstract · scifi · toon |
| Custom themes | `--theme FILE` / `--theme-url URL` | Merge JSON `{name: tokens}` into presets |
| Auto model routing | `--auto-model` | Short edits → haiku · long scenes → opus |
| Cost telemetry | `--cost` · `--cost-budget USD` | Per-call USD + batch-level kill switch |
| Scene diff | `--diff` | `+added` / `-removed` object names after send |
| Fast preview | `--preview` | 480×270 render + auto-open |
| Replay logs | `--history FILE` · `--save-state FILE` | JSONL for audit + replay |
| Quality rating | `--rate 1..5` | Append rating to history — the EvoSkillOps signal |
| EvoSkillOps report | `--skillops-report FILE` | Aggregate stats from history: top prompts, mean rating, model mix, cache-hit rate |
| EvoSkillOps export | `--skillops-export FILE` | Emit fine-tune-ready `{prompt, completion}` JSONL filtered by rating |
| Reliability | `--retry N` | Exponential backoff on transient API errors |
| Design rationale | `--explain` | Prepend `# Design rationale:` comment block |
| Dry run | `--dry-run` | Resolve model + prompt preview without burning tokens |
| Catalogs | `--list-presets` · `--list-demos` | Discovery with one command |
| Onboarding | `--doctor` · `--version` | Zero-config diagnostic + version stamp |

See [`CLAUDE.md`](./CLAUDE.md) for the full flag reference and [`AGENTS.md`](./AGENTS.md) for the agent-integration guide.

---

## The EvoSkillOps flywheel

Every run can append a JSONL history record of `{ts, model, prompt, script, rating?, tokens?, cost?}`. Rate the output 1–5 with `--rate`, aggregate with `--skillops-report`, then harvest the winners into a fine-tune-ready corpus with `--skillops-export`.

```bash
# 1. Generate + rate
python blender_gen.py "volumetric nebula with godrays" \
  --history runs.jsonl --rate 5

# 2. See what's working
python blender_gen.py --skillops-report runs.jsonl

# 3. Export your top-rated prompt/script pairs
python blender_gen.py --skillops-export corpus.jsonl \
  --history runs.jsonl --rate-min 4
```

The output of `--skillops-export` is directly shaped for supervised fine-tuning, few-shot libraries, or RAG indexes — your model gets better at *your* scenes every week.

---

## Space Metaverse demos

Geospatial, persistent 3D worlds built for Earth-observation storytelling (Galileo, Copernicus, KafCade mission briefs).

```bash
python blender_gen.py --list-demos
python blender_gen.py --demo earth --preview
python blender_gen.py --demo mars  --preview
python blender_gen.py --demo cyberpunk --preview
```

Each demo lands you in a scene labelled `UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY <NAME>` — the shared coordinate system for a persistent commercial 3D geo-world.

---

## Setup

Requires:

- **Python 3.9+** · `pip install anthropic`
- **`ANTHROPIC_API_KEY`** in your environment
- **Blender 4.x** + the [BlenderMCP add-on](https://github.com/ahujasid/blender-mcp) for `--send` / `--scene` / `--preview` / `--diff` / `--demo`

Blender side: open Blender, enable the BlenderMCP add-on, press **Connect to Claude** in the `N`-panel. Then every `--send` lands in that viewport.

---

## Standalone: `agent_seo`

The agent-SEO scaffolding is also shipped as a **standalone module** (`agent_seo.py`) you can drop into any project — zero deps, pure stdlib, ARM-safe. It emits the four files that make a codebase legible to AI agents and LLM crawlers (`llms.txt`, `llms-full.txt`, `AGENTS.md`, `.well-known/agents.json`) from one Python dataclass manifest.

```bash
# Scaffold a manifest template, edit it, regenerate SEO files anywhere
python agent_seo.py --init
python agent_seo.py manifest.py ./my-project
```

Library use:

```python
from agent_seo import AgentManifest, Capability, write_all
write_all(AgentManifest(name="my-tool", human="My Tool", summary="...",
                        repository="https://github.com/me/my-tool",
                        entry_point="my_tool.py"))
```

Ships the same spec `claude-blender` uses in production. Reuse it on every repo you want AI agents to discover and self-orient in.

---

## For AI coding agents

This repo is **agent-detectable by design**:

- [`AGENTS.md`](./AGENTS.md) — conventions for Cursor, Claude Code, Aider, Codex, and friends
- [`llms.txt`](./llms.txt) — [llmstxt.org](https://llmstxt.org/) index
- [`llms-full.txt`](./llms-full.txt) — full context for ingestion
- [`.well-known/agents.json`](./.well-known/agents.json) — self-describing capability manifest
- [`CLAUDE.md`](./CLAUDE.md) — project context consumed by Claude Code

If you are an agent reading this: start with `AGENTS.md`, then `CLAUDE.md`, then `blender_gen.py`.

---

## Roadmap

See [`claude_blender_Blueprint.md`](./claude_blender_Blueprint.md) for the full roadmap and version history. Current: **v0.19 — Onboarding · Modular Agent-SEO**.

---

## Citation

If you use claude-blender in research, please cite it:

```bibtex
@software{claude_blender,
  author  = {Nzengou, Désiré},
  title   = {claude-blender: Natural language to Blender via Claude},
  year    = {2026},
  url     = {https://github.com/dnzengou/claude-blender}
}
```

See [`CITATION.cff`](./CITATION.cff) for machine-readable metadata.

---

## License

MIT — see [`LICENSE`](./LICENSE).

---

**Keywords:** blender, bpy, claude, anthropic, mcp, llm, generative 3d, ai 3d, prompt-to-3d, text-to-3d, procedural, geospatial, space metaverse, galileo, copernicus, agents, llms.txt, agents.md, cli, python, arm64, apple silicon, raspberry pi, graviton.
