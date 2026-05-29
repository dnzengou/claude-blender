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
python blender_gen.py "add neon lights to scene" --scene --send   # live Blender
python blender_gen.py "forest floor low-poly" --stream -o forest.py
```

## Flags (v0.2)
| Flag | Effect |
|------|--------|
| `--send` | Execute script in running Blender via MCP socket (localhost:9876) |
| `--scene` | Fetch live scene state from Blender, inject into Claude prompt |
| `--stream` | Stream Claude output token-by-token to stdout |
| `--model` | `claude-opus-4-7` (default) / `sonnet-4-6` / `haiku-4-5` |
| `-o FILE` | Write script to file |

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
