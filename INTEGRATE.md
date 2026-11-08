# INTEGRATE.md — End-user Integrations

How to plug `claude-blender` into your environment, whatever that looks
like. One page, verifiable steps, no hand-waving.

If a step references a file in this repo, its path is the proof.

---

## 1. Local install (laptop or workstation)

```bash
git clone https://github.com/dnzengou/claude-blender.git
cd claude-blender
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                  # or set on Windows
python blender_gen.py "a spinning gold torus"
```

Verify: `python blender_gen.py --version` → `claude-blender 0.19.0`.

## 2. PyPI (once published)

```bash
pip install claude-blender
export ANTHROPIC_API_KEY=sk-ant-...
claude-blender "a spinning gold torus"
```

Metadata source: [`pyproject.toml`](./pyproject.toml). Console entry points
`claude-blender` and `blender-gen` are both registered.

## 3. Live Blender (BlenderMCP)

Prerequisite: the upstream add-on at
<https://github.com/ahujasid/blender-mcp>.

Steps:

1. Install the BlenderMCP add-on in Blender (`Edit → Preferences → Add-ons → Install`).
2. Open Blender's `N`-panel → BlenderMCP tab → click **Connect to Claude**.
3. Run `python blender_gen.py "<prompt>" --send`.

Defaults: `localhost:9876`. Change with `--host` / `--port`. Remote Blender
on a LAN works out of the box.

Compose flags:

```bash
python blender_gen.py "add neon lights" --send --scene --diff --preview
```

- `--scene` pulls Blender's current state into the prompt.
- `--diff` prints `+added` / `-removed` object names.
- `--preview` renders 480×270 PNG and opens it.

## 4. macOS

Any recent macOS on Apple Silicon or Intel works. Install Python via
Homebrew (`brew install python@3.12`) or the official installer. The
default viewer for `--preview` is handled by `open` (Preview.app).

## 5. Linux

Any mainstream distro. `--preview` uses `xdg-open`, so install `xdg-utils`
if you want preview auto-open. On ARM64 / AWS Graviton / Raspberry Pi 4+,
`pip install anthropic` resolves an `aarch64` wheel — no native build
required.

## 6. Windows

- Python 3.10+ from python.org or the Microsoft Store.
- A `cp1252` console is explicitly supported — `--help` was patched in
  v0.16 to stop crashing on UnicodeEncodeError (`stdout.reconfigure("utf-8")`
  at module load).
- `--preview` uses `os.startfile`.

## 7. GitHub Actions CI

The repo's own CI runs `ruff` + `py_compile` on push. Copy the shape:

```yaml
# .github/workflows/ci.yml (excerpt)
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install -r requirements.txt "ruff>=0.6,<0.18"
- run: ruff check blender_gen.py
- run: python -m py_compile blender_gen.py
```

Ruff is pinned to a range so default-rule drift doesn't break CI across
releases.

## 8. CI as a scene generator

You can run `claude-blender` in CI to generate scenes on PR for review.
`ANTHROPIC_API_KEY` must be stored as a repository secret.

```yaml
- name: Generate scenes
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    pip install claude-blender
    claude-blender --batch prompts.txt --output-dir ./scripts/ \
      --history runs.jsonl --cost-budget 0.50
```

`--cost-budget` is a kill switch for runaway spend.

## 9. EvoSkillOps flywheel

```bash
# 1. Generate + rate while you work
claude-blender "volumetric nebula with godrays" \
  --history runs.jsonl --rate 5

# 2. Read the aggregate stats
claude-blender --skillops-report runs.jsonl

# 3. Pipe JSON into a dashboard or alerting tool
claude-blender --skillops-report runs.jsonl --json | jq .mean_rating

# 4. Export your top-rated runs as a fine-tune-ready corpus
claude-blender --skillops-export corpus.jsonl \
  --history runs.jsonl --rate-min 4
```

The export is a simple JSONL of `{prompt, completion}` — drop it into:

- An Anthropic fine-tuning flow when available.
- A few-shot library (load the top-K into the system prompt).
- A RAG index (embed and retrieve on new prompts).

## 10. Theme packs

Local file:

```bash
claude-blender "arcade scene" --theme themes_example.json --preset vaporwave
```

Remote HTTPS gist (cached under `~/.blender_gen_themes/`):

```bash
claude-blender "arcade scene" --theme-url https://gist.github.com/.../themes.json --preset noir
```

## 11. Space Metaverse one-liner demos

```bash
claude-blender --list-demos
claude-blender --demo earth --preview
claude-blender --demo mars  --preview
claude-blender --demo cyberpunk --preview
```

Each demo prints a KafCade mission brief
(`UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY <NAME>`) and ships the
corresponding scene from `scenes/`.

## 12. Agents and automation

If you are an AI agent integrating with this repo, read
[`AGENTS.md`](./AGENTS.md) first, then
[`.well-known/agents.json`](./.well-known/agents.json) for a machine-readable
capability list.

For LLM search indexers:
[`llms.txt`](./llms.txt) and [`llms-full.txt`](./llms-full.txt).

For factual grounding: [`TRUST.md`](./TRUST.md) and [`FAQ.md`](./FAQ.md).

## 13. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ANTHROPIC_API_KEY` not set | env var missing | `export ANTHROPIC_API_KEY=sk-ant-...` |
| `Blender MCP not reachable on localhost:9876` | add-on not running | Open Blender → N-panel → BlenderMCP → Connect to Claude |
| `--help` crashes on Windows cp1252 | legacy stdio encoding | fixed in v0.16; update to latest |
| CI `ruff check` fails after version bump | rule-set drift | pin `"ruff>=0.6,<0.18"` as in this repo's CI |
| `--preview` doesn't open | missing `xdg-open` on Linux | `sudo apt install xdg-utils` |
| Rate-limited (429) | transient | add `--retry 3` for backoff |
