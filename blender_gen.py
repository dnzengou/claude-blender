"""
Generate Blender Python scripts from natural language via Claude API.
ARM-optimized: pure Python, zero native extensions.

Usage:
    python blender_gen.py "spinning torus with gold material"
    python blender_gen.py "procedural city grid 10x10" -o city.py
    python blender_gen.py "add lights around scene" --scene --send
    python blender_gen.py "solar system" --stream --model claude-sonnet-4-6
    python blender_gen.py --batch prompts.txt --output-dir ./scripts/
    python blender_gen.py "scatter rocks" --send --host 192.168.1.10 --port 9876
"""

import anthropic
import argparse
import json
import os
import socket
import sys
from pathlib import Path

MCP_TIMEOUT = 10  # seconds

SYSTEM_PROMPT = """You are a Blender Python scripting expert. Output complete, runnable bpy scripts only.
Rules:
- Start every script with: import bpy
- Clear existing scene objects when starting fresh: bpy.ops.wm.read_factory_settings(use_empty=True)
- Use only: bpy.data, bpy.ops, bpy.context — no external imports
- Scripts must run in Blender's Text Editor (Run Script button) or via socket execution
- Default to low-poly geometry unless the user specifies detail
- No placeholder comments like "# add more objects here" — complete the implementation
- Return ONLY the Python code, no prose, no markdown fences"""

# Cached system block — reused across all calls in a session.
# cache_control marks this as a prompt cache breakpoint (~80% cost on repeat hits).
SYSTEM_BLOCK = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]


# ── MCP socket helpers ────────────────────────────────────────────────────────

def _mcp_send(sock: socket.socket, payload: dict) -> dict:
    """Send one JSON request, read one JSON response (newline-delimited)."""
    sock.sendall((json.dumps(payload) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return json.loads(buf.strip())


def get_scene_info(host: str, port: int) -> str:
    """Return compact scene JSON from Blender MCP socket."""
    with socket.create_connection((host, port), timeout=MCP_TIMEOUT) as s:
        resp = _mcp_send(s, {"type": "get_scene_info"})
    if resp.get("status") == "error":
        raise RuntimeError(f"Blender MCP error: {resp.get('message')}")
    info = resp.get("result", resp)
    return json.dumps(info, indent=2) if isinstance(info, dict) else str(info)


def send_to_blender(code: str, host: str, port: int) -> str:
    """Execute a bpy script in running Blender via MCP socket."""
    with socket.create_connection((host, port), timeout=MCP_TIMEOUT) as s:
        resp = _mcp_send(s, {"type": "execute_code", "code": code})
    if resp.get("status") == "error":
        raise RuntimeError(f"Blender execution error: {resp.get('message')}")
    return resp.get("result", "")


# ── Claude generation ─────────────────────────────────────────────────────────

def generate_blender_script(prompt: str, model: str, stream: bool = False) -> str:
    """Call Claude with a cached system prompt. Returns complete bpy script."""
    client = anthropic.Anthropic()

    kwargs = dict(
        model=model,
        max_tokens=4096,
        system=SYSTEM_BLOCK,
        messages=[{"role": "user", "content": prompt}],
    )

    if stream:
        parts = []
        with client.messages.stream(**kwargs) as s:
            for text in s.text_stream:
                print(text, end="", flush=True)
                parts.append(text)
        print()
        return "".join(parts)

    response = client.messages.create(**kwargs)
    return response.content[0].text


def read_batch_prompts(path: str) -> list[str]:
    """Read non-empty, non-comment lines from a batch prompts file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


# ── single-prompt pipeline ────────────────────────────────────────────────────

def run_single(prompt: str, args) -> None:
    if args.scene:
        print("Fetching scene from Blender...", file=sys.stderr)
        try:
            scene_json = get_scene_info(args.host, args.port)
            prompt = f"Current Blender scene:\n{scene_json}\n\nTask: {prompt}"
        except (ConnectionRefusedError, OSError) as exc:
            print(f"Warning: cannot reach Blender MCP ({exc}). Ignoring --scene.", file=sys.stderr)

    script = generate_blender_script(prompt, args.model, stream=args.stream)

    if args.output:
        _write_file(args.output, script)
    elif not args.stream:
        print(script)

    if args.send:
        _send(script, args.host, args.port)


# ── batch pipeline ────────────────────────────────────────────────────────────

def run_batch(prompts: list[str], args) -> None:
    out_dir = Path(args.output_dir) if args.output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(args.batch).stem
    total = len(prompts)

    for i, prompt in enumerate(prompts, start=1):
        print(f"[{i}/{total}] {prompt[:60]}", file=sys.stderr)
        script = generate_blender_script(prompt, args.model)  # no stream in batch
        out_path = out_dir / f"{stem}_{i:03d}.py"
        _write_file(str(out_path), script)

        if args.send:
            _send(script, args.host, args.port)


# ── shared helpers ────────────────────────────────────────────────────────────

def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {path}", file=sys.stderr)


def _send(script: str, host: str, port: int) -> None:
    print(f"Sending to Blender ({host}:{port})...", file=sys.stderr)
    try:
        result = send_to_blender(script, host, port)
        if result:
            print(f"Blender: {result}", file=sys.stderr)
        print("Done.", file=sys.stderr)
    except (ConnectionRefusedError, OSError):
        print(
            f"Error: Blender MCP not reachable on {host}:{port}.\n"
            "Start Blender, enable BlenderMCP add-on, click 'Connect to Claude'.",
            file=sys.stderr,
        )
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude → Blender: natural language to bpy scripts"
    )

    # Mutually exclusive input modes
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("prompt", nargs="?", help="What to build in Blender")
    input_group.add_argument("--batch", metavar="FILE", help="File of prompts (one per line)")

    parser.add_argument(
        "--model",
        default="claude-opus-4-7",
        choices=["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        help="Claude model (default: opus-4-7)",
    )
    parser.add_argument("--output", "-o", metavar="FILE", help="Save script to file (single mode)")
    parser.add_argument("--output-dir", metavar="DIR", help="Output directory for batch mode")
    parser.add_argument("--send", action="store_true", help="Execute script(s) in Blender via MCP socket")
    parser.add_argument("--scene", action="store_true", help="Inject live Blender scene state into prompt")
    parser.add_argument("--stream", action="store_true", help="Stream Claude output to stdout")
    parser.add_argument("--host", default="localhost", help="Blender MCP host (default: localhost)")
    parser.add_argument("--port", type=int, default=9876, help="Blender MCP port (default: 9876)")

    args = parser.parse_args()

    if args.batch:
        prompts = read_batch_prompts(args.batch)
        if not prompts:
            print("Error: batch file is empty.", file=sys.stderr)
            sys.exit(1)
        run_batch(prompts, args)
    else:
        run_single(args.prompt, args)


if __name__ == "__main__":
    main()
