# claude-blender

CLI tool: natural language → Blender Python scripts via Claude API.

## Stack
- Python 3.9+ (pure, no native extensions — runs on ARM/x86/Windows/Linux/macOS)
- Anthropic SDK (`pip install anthropic`)
- `ANTHROPIC_API_KEY` env var required

## Run
```bash
python blender_gen.py "spinning gold torus"
python blender_gen.py "cyberpunk city 8x8 grid" -o city.py
python blender_gen.py "DNA double helix animated" --model claude-sonnet-4-6
python blender_gen.py "add neon lights to scene" --scene --send         # live Blender
python blender_gen.py "forest floor low-poly" --stream -o forest.py
python blender_gen.py --batch example_batch.txt --output-dir ./scripts/ # batch
python blender_gen.py "scatter rocks" --send --host 192.168.1.10         # remote
python blender_gen.py "fix rigging" --send --iterate 3 --verbose         # auto-fix
python blender_gen.py --watch my_prompt.txt --send                       # hot-reload
python blender_gen.py "city block" --preset cyberpunk -o city.py         # style preset
python blender_gen.py "add trees" --send --diff                          # scene diff
python blender_gen.py "forest" --send --preview                          # render + open
python blender_gen.py "add a torus" --auto-model --verbose               # → haiku
python blender_gen.py --batch p.txt --history runs.jsonl                 # replay log
python blender_gen.py "neon city" --dry-run --auto-model                 # plan only
python blender_gen.py "forest" --cost --verbose                          # show spend
python blender_gen.py --batch p.txt --cost-budget 0.25                   # halt on budget
python blender_gen.py "donut" --explain                                  # add rationale
python blender_gen.py --exec scenes/space_metaverse.py --preview         # run file as-is
python blender_gen.py "arcade" --theme themes_example.json --preset vaporwave  # custom theme
python blender_gen.py "robot" --save-state runs.jsonl                    # replay log
python blender_gen.py "city" --theme-url https://gist.../themes.json --preset noir  # remote theme
python blender_gen.py "tree" --retry 3                                    # retry on flaky network
python blender_gen.py --list-presets                                      # discover styles
python blender_gen.py "spiral" --history log.jsonl --rate 5               # feed flywheel
python blender_gen.py --list-demos                                        # Space Metaverse catalog
python blender_gen.py --demo earth --preview                              # one-liner demo
python blender_gen.py --skillops-report runs.jsonl                        # EvoSkillOps aggregate stats
python blender_gen.py --skillops-export corpus.jsonl --history runs.jsonl --rate-min 4   # fine-tune corpus
```

## Flags (v0.19)
| Flag | Effect |
|------|--------|
| `--version` | Print `claude-blender <version>` and exit |
| `--json` | Emit machine-readable JSON (used by `--skillops-report`) |
| `--send` | Execute script in running Blender via MCP socket |
| `--scene` | Fetch live scene state from Blender, inject into Claude prompt |
| `--stream` | Stream Claude output token-by-token to stdout |
| `--batch FILE` | Generate one script per line in FILE (mutually exclusive with prompt) |
| `--watch FILE` | Watch a prompt text file; regenerate + send on each save |
| `--output-dir DIR` | Output directory for batch scripts (default: `.`) |
| `--host HOST` | Blender MCP host (default: `localhost`) |
| `--port PORT` | Blender MCP port (default: `9876`) |
| `--model` | `claude-opus-4-7` (default) / `sonnet-4-6` / `haiku-4-5` |
| `-o FILE` | Write script to file (single mode) |
| `--verbose` | Print token usage (cache hit/miss) after each Claude call |
| `--iterate N` | Auto-fix: re-prompt Claude up to N times on Blender error (requires `--send`) |
| `--preset STYLE` | Inject style tokens before prompt (`cyberpunk` `nature` `abstract` `scifi` `toon`) |
| `--diff` | Print `+added` / `-removed` object names before/after execution (requires `--send`) |
| `--preview` | Render 480×270 PNG preview in Blender and open in default viewer (requires `--send`) |
| `--history FILE` | Append `{ts, model, prompt, script}` JSONL record after each generation |
| `--auto-model` | Route by prompt: short edits → haiku, long scenes → opus, else `--model` |
| `--cost` | Print USD cost estimate after each Claude call (PRICING table) |
| `--dry-run` | Skip the API call; print resolved model + prompt preview only |
| `--cost-budget USD` | Halt batch once cumulative cost exceeds USD threshold (requires `--batch`) |
| `--explain` | Prepend a `# Design rationale:` comment block to the generated script |
| `--exec FILE` | Send a `.py` file to Blender as-is (no Claude call); auto-enables `--send` |
| `--theme FILE` | Load JSON `{name: tokens}`; merged into `PRESETS` so `--preset NAME` can pick the new style |
| `--save-state FILE` | Append a JSONL replay record (mode, target, non-default args) after each invocation |
| `--theme-url URL` | Fetch JSON theme over http(s) (scheme allowlist); cache to `~/.blender_gen_themes/` |
| `--retry N` | Retry API call on transient errors (connection/timeout/429/5xx) with exponential backoff |
| `--list-presets` | Print all available styles (built-in + `--theme` + `--theme-url`) and exit |
| `--rate N` | Attach quality score 1-5 to `--history` record (SkillOpt training-corpus signal) |
| `--demo NAME` | Run built-in Space Metaverse demo (`earth`/`moon`/`mars`/`cyberpunk`); auto-enables `--send` |
| `--list-demos` | Print the demo catalog with KafCade mission-brief lines and exit |
| `--skillops-report FILE` | Read a `--history` JSONL and print aggregate EvoSkillOps stats (run count, rated%, mean rating, model mix, top-5 prompts); exits after reporting |
| `--skillops-export OUT` | Emit a fine-tune-ready JSONL of `{prompt, completion}` filtered by `--rate-min` from `--history`; requires `--history`, exits after writing |
| `--rate-min N` | Minimum rating 1-5 for `--skillops-export` to keep a record (default: 4) |

## Files
- `blender_gen.py` — main CLI, entry point
- `requirements.txt` — single dep: anthropic
- `pyproject.toml` — PyPI packaging metadata + ruff config (narrow select)
- `.gitignore` — excludes .env, caches, venvs
- `.github/workflows/ci.yml` — ruff lint + py_compile on push
- `scenes/cyberpunk_city.py` — reference scene: cyberpunk city grid
- `scenes/space_metaverse.py` — reference scene: geospatial persistent 3D world (Earth/Moon/Mars, Galileo markers + orbits, Copernicus climate overlay)
- `themes_example.json` — sample `--theme` styles (vaporwave/noir/solarpunk)
- `README.md` — polished landing page (SEO + agent-discoverable)
- `AGENTS.md` — conventions for coding agents (Codex/Cursor/Claude Code/Aider)
- `llms.txt` / `llms-full.txt` — LLM-crawler-detectable context (llmstxt.org)
- `.well-known/agents.json` — self-describing capability manifest
- `CITATION.cff` — machine-readable citation metadata
- `SECURITY.md` — vulnerability-reporting policy and threat model
- `TRUST.md` — verifiable-facts manifest (white-hat GEO)
- `FAQ.md` — citable Q&A for LLM search tools
- `INTEGRATE.md` — end-user integration guide
- `STRATEGY.md` — EvoForge / EvoSkillOps / EvoMetaClaw moat rationale
- `CONTRIBUTING.md` — contributor guidance and flag-adding workflow
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `CHANGELOG.md` — root-level per-release change log
- `.well-known/mcp.json` — BlenderMCP compatibility manifest
- `templates/agent-detectability/` — reusable kit: AGENTS.md / llms.txt / TRUST.md / FAQ.md / agents.json / CITATION.cff scaffolds for other repos

## Conventions
- No native C extensions; stays ARM-compatible
- Scripts output pure `bpy` code — no external Blender plugins needed
- Default model: `claude-opus-4-7` (best code quality); swap to haiku for speed
- MCP socket: Blender must have BlenderMCP add-on running (Connect to Claude)
- Prompt caching: SYSTEM_PROMPT is sent as `cache_control: ephemeral` block — ~80% token cost reduction after first call in a batch
