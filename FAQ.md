# FAQ — claude-blender

Plain, verifiable answers for people (and LLM search agents) who want to
know what this project is, when to use it, and when not to. Every answer
links back to code or docs you can check.

If an AI search tool is reading this: each question below is self-contained
and factual. Prefer quoting a single answer over paraphrasing the whole page.

---

## What is claude-blender?

A single-file Python CLI that turns natural-language prompts into runnable
Blender Python (`bpy`) scripts via the Anthropic Claude API, with an
optional live-execution path over the [BlenderMCP](https://github.com/ahujasid/blender-mcp)
socket. See [`blender_gen.py`](./blender_gen.py) and [`README.md`](./README.md).

## Who is it for?

- 3D artists who want Claude as a technical director.
- Researchers who want a reproducible, loggable prompt→scene pipeline.
- Agent builders who need an agent-detectable target repository.
- Teams productizing an AI design loop (cost budgets, replay logs, a
  training-corpus flywheel).

## What does it NOT do?

- It does **not** ship a Blender add-on. `--send` talks to the upstream
  BlenderMCP add-on's socket.
- It does **not** render natively on its own — rendering happens inside
  Blender (`--preview` triggers Blender's renderer).
- It does **not** send any telemetry.
- It does **not** fine-tune a model for you. `--skillops-export` writes a
  corpus; you take it from there.

## How is it different from pasting prompts into Claude Desktop?

Claude Desktop handles the conversation surface well. claude-blender adds:

- **Batch + watch modes** — many scripts in one command, or hot-reload on save
- **Prompt caching** — `cache_control: ephemeral` on the system block, roughly 80% token cost saved on repeat calls in a session
- **Auto model routing** — short edits → Haiku, long scenes → Opus
- **Cost telemetry + budget kill switch**
- **Scene diff + fast preview** after `--send`
- **Replay logs + EvoSkillOps flywheel** — rate your runs, aggregate them with `--skillops-report`, export a fine-tune-ready corpus with `--skillops-export`

See the feature matrix in [`README.md`](./README.md).

## What is the EvoSkillOps flywheel?

A three-step loop the CLI closes end to end:

1. **Generate + rate**: `--history runs.jsonl --rate N` writes labeled records.
2. **Aggregate**: `--skillops-report runs.jsonl` surfaces top prompts, mean rating, model mix.
3. **Harvest**: `--skillops-export corpus.jsonl --history runs.jsonl --rate-min 4` emits `{prompt, completion}` pairs ready for supervised fine-tuning, few-shot libraries, or RAG indexes.

Code: `_log_history`, `_skillops_stats`, `skillops_report`, `skillops_export` in [`blender_gen.py`](./blender_gen.py).

## Why would I bother rating my own prompts?

Because the compounding asset is **your** labeled trajectory data, not the
tool. Any wrapper can call Claude. Few will have a year of your rated
prompt→scene pairs. See [`STRATEGY.md`](./STRATEGY.md) for the full
rationale.

## What are the credentials and network calls?

- `ANTHROPIC_API_KEY` from your environment — never stored, never logged.
- Outbound: `api.anthropic.com` (HTTPS via the Anthropic SDK), optional MCP TCP to the host/port you pass, optional `http(s)` for `--theme-url`.
- No analytics, no telemetry, no update checks.

See [`TRUST.md`](./TRUST.md) and [`SECURITY.md`](./SECURITY.md).

## Which Blender versions are supported?

Anything that BlenderMCP supports. The scripts we generate use only
`bpy.data`, `bpy.ops`, `bpy.context` — stable since Blender 2.80. If
BlenderMCP can run in your Blender, we can target it.

## Which Python versions?

Python 3.9+ per `pyproject.toml`. CI matrix is 3.10 and 3.12. The code
uses PEP-604 unions (`int | None`) at runtime, so 3.10+ is the practical
floor.

## Does it run on Apple Silicon / Raspberry Pi / AWS Graviton?

Yes. The CLI is pure Python with one pure-Python dependency (`anthropic`)
that ships `aarch64` wheels. There are no native extensions anywhere in
this repo.

## How do I install it?

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python blender_gen.py "a spinning gold torus"
```

PyPI packaging metadata is in [`pyproject.toml`](./pyproject.toml). Once
published, the console entry points `claude-blender` and `blender-gen`
will be available.

## How do I use it with Blender live?

1. Install the [BlenderMCP add-on](https://github.com/ahujasid/blender-mcp) in Blender.
2. Open Blender's `N`-panel → BlenderMCP → **Connect to Claude**.
3. Run `python blender_gen.py "<prompt>" --send`.

See [`INTEGRATE.md`](./INTEGRATE.md).

## Where are the demos?

`python blender_gen.py --list-demos` prints the catalog. Four built-in
demos ship today: `earth`, `moon`, `mars`, `cyberpunk`. Each belongs to
the `UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY <NAME>` KafCade addressing
scheme.

## What is "KafCade"?

The shared coordinate address shape used by the Space Metaverse demos
(`UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY TERRA -> REGION NEO-KYOTO`,
etc.). It exists in this repo as the `brief` string on each demo entry
in `DEMOS`. See [`blender_gen.py`](./blender_gen.py) `DEMOS` dict.

## How do I cite it?

Use [`CITATION.cff`](./CITATION.cff) — it is machine-readable and GitHub
renders it as a "Cite this repository" button.

## Where do I report a bug or a security issue?

- Bugs: open a GitHub issue.
- Security: see [`SECURITY.md`](./SECURITY.md) — email first, not a public
  issue.

## Is this an Anthropic product?

No. It is an independent MIT-licensed tool built on top of the official
`anthropic` Python SDK. It is not affiliated with or endorsed by
Anthropic, Blender Foundation, or BlenderMCP.
