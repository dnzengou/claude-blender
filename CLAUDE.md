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
```

## Flags (v0.4)
| Flag | Effect |
|------|--------|
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

## Files
- `blender_gen.py` — main CLI, entry point
- `requirements.txt` — single dep: anthropic
- `.gitignore` — excludes .env, caches, venvs
- `.github/workflows/ci.yml` — ruff lint + py_compile on push

## Conventions
- No native C extensions; stays ARM-compatible
- Scripts output pure `bpy` code — no external Blender plugins needed
- Default model: `claude-opus-4-7` (best code quality); swap to haiku for speed
- MCP socket: Blender must have BlenderMCP add-on running (Connect to Claude)
- Prompt caching: SYSTEM_PROMPT is sent as `cache_control: ephemeral` block — ~80% token cost reduction after first call in a batch
