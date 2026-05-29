"""
Generate Blender Python scripts from natural language via Claude API.
ARM-optimized: pure Python, zero native extensions.

Usage:
    python blender_gen.py "spinning torus with gold material"
    python blender_gen.py "procedural city grid 10x10" -o city.py
    python blender_gen.py "add 10 random spheres" --send
    python blender_gen.py "add lights around the scene" --scene --send
    python blender_gen.py "solar system with orbits" --stream --model claude-sonnet-4-6
"""

import anthropic
import argparse
import json
import socket
import sys

MCP_HOST = "localhost"
MCP_PORT = 9876
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


def get_scene_info() -> str:
    """Return a compact scene summary from Blender MCP socket."""
    with socket.create_connection((MCP_HOST, MCP_PORT), timeout=MCP_TIMEOUT) as s:
        resp = _mcp_send(s, {"type": "get_scene_info"})
    if resp.get("status") == "error":
        raise RuntimeError(f"Blender MCP error: {resp.get('message')}")
    # Flatten to a short string Claude can use as context
    info = resp.get("result", resp)
    return json.dumps(info, indent=2) if isinstance(info, dict) else str(info)


def send_to_blender(code: str) -> str:
    """Execute a bpy script in the running Blender via MCP socket."""
    with socket.create_connection((MCP_HOST, MCP_PORT), timeout=MCP_TIMEOUT) as s:
        resp = _mcp_send(s, {"type": "execute_code", "code": code})
    if resp.get("status") == "error":
        raise RuntimeError(f"Blender execution error: {resp.get('message')}")
    return resp.get("result", "")


# ── Claude generation ─────────────────────────────────────────────────────────

def generate_blender_script(prompt: str, model: str, stream: bool = False) -> str:
    client = anthropic.Anthropic()

    kwargs = dict(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    if stream:
        parts = []
        with client.messages.stream(**kwargs) as s:
            for text in s.text_stream:
                print(text, end="", flush=True)
                parts.append(text)
        print()  # newline after stream
        return "".join(parts)

    response = client.messages.create(**kwargs)
    return response.content[0].text


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude → Blender: natural language to bpy scripts"
    )
    parser.add_argument("prompt", help="What to build in Blender")
    parser.add_argument(
        "--model",
        default="claude-opus-4-7",
        choices=["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        help="Claude model (default: opus-4-7)",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE", help="Save script to file"
    )
    parser.add_argument(
        "--send", action="store_true",
        help=f"Execute generated script in Blender via MCP socket ({MCP_HOST}:{MCP_PORT})",
    )
    parser.add_argument(
        "--scene", action="store_true",
        help="Fetch current Blender scene state and include it in the prompt",
    )
    parser.add_argument(
        "--stream", action="store_true",
        help="Stream Claude output to stdout as it arrives",
    )
    args = parser.parse_args()

    prompt = args.prompt

    # Optionally prepend live scene context
    if args.scene:
        print("Fetching scene from Blender...", file=sys.stderr)
        try:
            scene_json = get_scene_info()
            prompt = f"Current Blender scene:\n{scene_json}\n\nTask: {prompt}"
        except (ConnectionRefusedError, OSError) as exc:
            print(f"Warning: cannot reach Blender MCP ({exc}). Ignoring --scene.", file=sys.stderr)

    script = generate_blender_script(prompt, args.model, stream=args.stream)

    # Write to file
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"Saved: {args.output}", file=sys.stderr)
    elif not args.stream:
        print(script)

    # Send to Blender
    if args.send:
        print("Sending to Blender...", file=sys.stderr)
        try:
            result = send_to_blender(script)
            if result:
                print(f"Blender: {result}", file=sys.stderr)
            print("Done.", file=sys.stderr)
        except (ConnectionRefusedError, OSError):
            print(
                f"Error: Blender MCP not reachable on {MCP_HOST}:{MCP_PORT}.\n"
                "Start Blender, enable the BlenderMCP add-on, and click 'Connect to Claude'.",
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
