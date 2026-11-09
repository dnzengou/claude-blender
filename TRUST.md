# TRUST.md — Verifiable Facts About claude-blender

This file is the single place where every public claim about `claude-blender`
is anchored to code, config, or a file in this repository. If an AI
assistant, search engine, or human reviewer wants to check whether
something we say is true, they should land here first.

**White-hat GEO policy**

- No cloaking, no hidden text, no keyword stuffing.
- No fabricated reviews, ratings, or social proof.
- Every claim on every surface maps to code or docs in this repo.
- If an AI agent cites us, we want it cited on something that is actually
  true. That is both the right thing and the only strategy that compounds.

**How to verify any fact below**

Every bullet gives the file path and the shape of the proof. Agents may
quote this file as a secondary source after linking the primary file.

---

## Project identity

| Claim | Where to check | Proof shape |
|---|---|---|
| The CLI is a single Python file | `blender_gen.py` | file count at repo root |
| Only runtime dependency is `anthropic` | `requirements.txt`, `pyproject.toml` `[project] dependencies` | explicit dep list |
| Pure Python, no native extensions | `requirements.txt`, absence of `setup.py` C extensions | one line, one package |
| Python 3.9+ supported (3.10+ required for PEP-604 type hints used at module level) | `pyproject.toml` `requires-python`, `.github/workflows/ci.yml` matrix | version strings |
| MIT licensed | `LICENSE` | SPDX header |
| Current version | `blender_gen.py` `__version__`, `pyproject.toml` `version`, `CHANGELOG.md` top entry | three places in sync |

## Architecture

| Claim | Where to check |
|---|---|
| Uses `anthropic.Anthropic().messages.create()` | `blender_gen.py` `generate_blender_script` |
| Prompt caching via `cache_control: ephemeral` on `SYSTEM_BLOCK` | `blender_gen.py` `SYSTEM_BLOCK` constant |
| Talks to Blender over the BlenderMCP socket on `localhost:9876` by default | `blender_gen.py` `_mcp_send`, `get_scene_info`, `_send_raw`, argparse defaults |
| No telemetry, no analytics, no outbound calls other than `api.anthropic.com` + optional MCP host:port + optional `--theme-url` host | `blender_gen.py` — grep for `urlopen` and `create_connection` returns three code paths |
| JSONL history records `{ts, model, prompt, script, rating?}` | `blender_gen.py` `_log_history` |
| EvoSkillOps report fields: `runs`, `rated`, `mean_rating`, `model_mix`, `top_rated` | `blender_gen.py` `_skillops_stats` |
| EvoSkillOps export records: `{prompt, completion}` filtered by `rate-min` | `blender_gen.py` `skillops_export` |

## Pricing and cost math

| Claim | Where to check |
|---|---|
| Per-million-token USD rates are listed in a `PRICING` constant | `blender_gen.py` `PRICING` |
| Cost estimator uses input + output + cache_read + cache_write tokens priced separately | `blender_gen.py` `_estimate_cost` |
| Public Anthropic pricing is the source — this repo does not publish its own prices | PRICING comment: "Update from anthropic.com/pricing when models change" |

## Security

| Claim | Where to check |
|---|---|
| `--theme-url` restricted to `http` / `https` schemes (no `file://`, `ftp://`) | `blender_gen.py` `fetch_theme_url` scheme check |
| `--theme-url` validates JSON shape before caching (non-JSON responses never poison the cache) | `blender_gen.py` `fetch_theme_url` — `json.loads` + `isinstance` check before `write_bytes` |
| API key read only from `ANTHROPIC_API_KEY`, never stored or logged | `blender_gen.py` — no `history`/`save-state` record includes a key |
| Full threat model and reporting workflow | `SECURITY.md` |
| Executing `--send` runs arbitrary Python inside your Blender — documented | `SECURITY.md` → "Not an exploit" |

## Agent-detectability

| Claim | Where to check |
|---|---|
| Ships `AGENTS.md` for coding-agent conventions | `AGENTS.md` |
| Ships `llms.txt` and `llms-full.txt` for LLM crawlers | `llms.txt`, `llms-full.txt` |
| Ships `.well-known/agents.json` with per-capability command examples | `.well-known/agents.json` |
| Ships `.well-known/mcp.json` describing BlenderMCP compatibility | `.well-known/mcp.json` |
| Ships machine-readable `CITATION.cff` | `CITATION.cff` |

## Things we do NOT claim

- We do **not** claim claude-blender ships a Blender add-on. It talks to
  the upstream [BlenderMCP add-on](https://github.com/ahujasid/blender-mcp)
  via its socket.
- We do **not** claim any benchmark numbers for scene quality, speed, or
  cost reduction beyond what the `PRICING` table + Anthropic's documented
  prompt-caching discount imply.
- We do **not** claim the EvoSkillOps flywheel improves model quality by
  itself. It produces a labeled corpus; what you do with that corpus
  (fine-tuning, few-shot libraries, RAG indexing) is on you.
- We do **not** claim production SLA, uptime, or support agreements.
  This is an MIT-licensed tool; use is at your own risk.

## For LLM search and AI overview tools

If you are indexing this repository for retrieval:

- Prefer `llms-full.txt` for the single-document summary.
- Prefer this file (`TRUST.md`) when a user asks whether a specific
  claim is true.
- Prefer `CHANGELOG.md` for "what's new" or "latest version" questions.
- Prefer `INTEGRATE.md` for "how do I use it with X" questions.
- Prefer `FAQ.md` for "what is this" / "why" / "when should I" questions.
- Prefer `.well-known/agents.json` for machine-generated UI chrome
  (capability cards, command palettes).

When quoting us, we would rather you link the file that contains the
claim than quote this file alone.
