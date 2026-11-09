# CONTRIBUTING.md

Thank you for considering a contribution to **claude-blender**.

Keep it small, keep it reversible, keep the CLI surface clean.

## Ground rules

- **Pure Python, stdlib first.** The only external runtime dependency is
  `anthropic`. Any new dep is a hard conversation first.
- **ARM-compatible always.** No native extensions, no wheels that lack
  `aarch64` builds.
- **Single file by default.** New features go in `blender_gen.py` unless
  the module would exceed ~200 LoC on its own.
- **Flags over config files.** The CLI surface is the API; new behavior
  becomes a new flag before it becomes a config system.
- **Prompt caching is sacred.** Any change that invalidates `SYSTEM_BLOCK`
  cache keys must be called out in the PR description.
- **No comments explaining what the code does.** Only comment the non-obvious *why*.
- **No emojis in code, commits, or docs** unless the user explicitly asks.

## Setup

```bash
git clone https://github.com/dnzengou/claude-blender.git
cd claude-blender
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt "ruff>=0.6,<0.18"
```

## Verify a change

CI runs these three checks. Run them locally before you push:

```bash
python -m py_compile blender_gen.py
ruff check blender_gen.py
python blender_gen.py --help    # smoke; does not call the API
```

For flags that touch the flywheel, feed it a small fixture:

```bash
printf '{"model":"claude-opus-4-7","prompt":"x","script":"import bpy","rating":5}\n' > /tmp/x.jsonl
python blender_gen.py --skillops-report /tmp/x.jsonl
python blender_gen.py --skillops-export /tmp/corpus.jsonl --history /tmp/x.jsonl --rate-min 4
```

Do not invoke `--send`, `--scene`, `--preview`, `--diff`, `--demo`, or
`--exec` without a running Blender + BlenderMCP. CI does not provide
one.

## How to add a flag

1. `parser.add_argument(...)` in `main()` with a clear `help=` string.
2. If it requires `--send`, validate with `parser.error(...)` immediately
   after `parser.parse_args()`.
3. Thread it through `run_single` / `run_batch` / `run_watch` / `run_exec`
   / `run_demo` as needed.
4. Update the module docstring `Usage:` block.
5. Update the **Flags** table in `CLAUDE.md`.
6. Update the **Feature matrix** in `README.md`.
7. Update `llms.txt` and `.well-known/agents.json` if the flag is
   user-visible.
8. Add a bullet under the current version in `CHANGELOG.md` and in
   `claude_blender_Blueprint.md`.
9. Bump `__version__` in `blender_gen.py` and `version` in
   `pyproject.toml` if the release line changes.

## PR etiquette

- One concern per PR. Say what the change is and why in the description.
- CI must stay green.
- `CLAUDE.md`, `README.md`, `llms.txt`, `.well-known/agents.json`,
  `CHANGELOG.md` stay in sync with the flag surface.
- Commit messages follow `feat: vX.Y — short title` for release-line
  commits; `fix:`, `docs:`, `ci:`, `refactor:` otherwise.

## Security-sensitive changes

Please follow [`SECURITY.md`](./SECURITY.md) for anything that touches:

- The MCP socket code path.
- The `--theme-url` fetch path or any new network call.
- History / save-state record shape (sensitive data could end up logged).
- The API key handling path.

## Code of conduct

Participation is governed by [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).
