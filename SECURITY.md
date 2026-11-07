# Security Policy

## Supported versions

Only the latest `main` branch of **claude-blender** receives security fixes.
Pinned installs older than the current minor version are unsupported.

## Reporting a vulnerability

Please report security issues privately, **not** in a public GitHub issue.

- Email: desire.yavro@gmail.com
- Subject line: `[claude-blender security] <short summary>`

Expected response window: **72 hours** to acknowledge, then a fix
timeline based on severity.

## Threat model and scope

`claude-blender` is a CLI that:

1. Reads an **Anthropic API key** from the `ANTHROPIC_API_KEY` environment
   variable and never persists it.
2. Sends prompts to `api.anthropic.com` over HTTPS (TLS via the Anthropic
   SDK).
3. Optionally connects to the **BlenderMCP socket** (default
   `localhost:9876`) and executes generated Python inside the running
   Blender via the MCP `execute_code` RPC.
4. Reads `--theme` JSON files from disk and `--theme-url` payloads over
   **http/https only** (scheme is validated — `file://`, `ftp://`, etc.
   are rejected); downloads are cached under `~/.blender_gen_themes/`.
5. Appends JSONL records via `--history` and `--save-state` locally.

In scope:

- Prompt or theme payloads that escape expected shapes and cause arbitrary
  code paths to be exercised.
- MCP socket handling (we only trust the host:port you point us at).
- Secret leakage through logs, history, or save-state records.
- Scheme / SSRF-shaped bypasses in `--theme-url`.

Out of scope:

- Blender add-on security itself (upstream BlenderMCP).
- Risks introduced by choosing to run **generated** Blender Python — any
  `--send`-enabled invocation executes arbitrary bpy code inside your
  running Blender. That is the tool's job. Treat prompts from untrusted
  parties accordingly.
- Third-party model safety (Anthropic handles the model layer).

## Agent-attack surface

If you operate `claude-blender` behind an autonomous agent, note:

- The agent can author prompts that run arbitrary bpy inside your
  Blender via `--send`.
- The agent can author batch files consumed by `--batch`.
- The agent can point `--theme-url` at any http/https origin.
- Isolate the Blender instance (sandbox, ephemeral profile) when exposing
  the CLI to untrusted prompt sources.

## Not an exploit

- "Generated bpy does something unexpected" — that is a model-quality
  issue, not a security vulnerability.
- "`--send` runs arbitrary Python in Blender" — documented and intended.
