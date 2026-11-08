# claude-blender

**Natural language → Blender Python scripts, powered by Claude.** One CLI. Zero plugins. Any machine, any CPU.

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

- **Pure Python.** No native extensions. Runs on Apple Silicon, Raspberry Pi, AWS Graviton, x86.
- **Prompt-cached system block.** ~80% token-cost reduction after the first call in a batch.
- **Live scene round-trip.** `--scene` pulls the current Blender state back into the prompt; `--send` pushes the generated script back into the viewport.
- **Space Metaverse ready.** Built-in `--demo earth|moon|mars|cyberpunk` ships a geospatial 3D world in one command — Galileo markers, orbit curves, Copernicus climate overlay.
- **Commercial surface.** Theme packs, cost budgets, replay logs, EvoSkillOps flywheel — the plumbing you need to productize an AI design loop.
- **Agent-detectable.** Ships `AGENTS.md`, `llms.txt`, `llms-full.txt`, and `.well-known/agents.json` so coding agents and LLM crawlers discover and self-orient here without hand-holding.

---

## Quickstart

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

# One-shot: print bpy script to stdout
python blender_gen.py "a spinning gold torus on a marble pedestal"

# Save to file
python blender_gen.py "cyberpunk city 8x8 grid" -o city.py

# Live Blender (requires BlenderMCP add-on + 'Connect to Claude' pressed in Blender)
python blender_gen.py "add neon lights to the scene" --scene --send

# One-liner value demo — ships a geospatial Earth scene
python blender_gen.py --demo earth --preview
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

See [`claude_blender_Blueprint.md`](./claude_blender_Blueprint.md) for the full roadmap and version history. Current: **v0.18 — EvoSkillOps · Agent-Detectable SEO**.

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
