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
    python blender_gen.py "fix this mesh" --send --iterate 3 --verbose
    python blender_gen.py --watch prompt.txt --send
    python blender_gen.py "city block" --preset cyberpunk -o city.py
    python blender_gen.py "add trees" --send --diff
"""

import anthropic
import argparse
import json
import socket
import sys
import time
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

# Style presets — prepended to the user prompt before Claude sees it.
# Keys must stay lowercase (CLI choices are lowercase).
PRESETS: dict[str, str] = {
    "cyberpunk": "Style: neon-lit cyberpunk aesthetic — glowing emissive materials in cyan/magenta/yellow, dark metallic surfaces, wet reflective ground, volumetric fog. ",
    "nature":    "Style: organic low-poly nature scene — earth tones, subsurface scattering on foliage, soft diffuse lighting, no sharp edges. ",
    "abstract":  "Style: abstract geometric art — bold primary colors, hard-edge materials, dramatic directional lighting, mathematical precision. ",
    "scifi":     "Style: hard-surface sci-fi — metallic panels with subtle emission, modular geometry, cool blue/white lighting, clean industrial aesthetic. ",
    "toon":      "Style: toon-shaded cartoon — flat colors with Toon BSDF, thick outlines via Solidify modifier, bright saturated palette, no cast shadows. ",
}


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


def _send_raw(code: str, host: str, port: int) -> tuple:
    """Execute script; returns (success: bool, result_or_error: str). Raises OSError on connect failure."""
    with socket.create_connection((host, port), timeout=MCP_TIMEOUT) as s:
        resp = _mcp_send(s, {"type": "execute_code", "code": code})
    if resp.get("status") == "error":
        return False, resp.get("message", "unknown error")
    return True, resp.get("result", "")


def send_to_blender(code: str, host: str, port: int) -> str:
    """Execute a bpy script in running Blender via MCP socket."""
    ok, msg = _send_raw(code, host, port)
    if not ok:
        raise RuntimeError(f"Blender execution error: {msg}")
    return msg


# ── scene diff helpers ────────────────────────────────────────────────────────

def _scene_object_names(scene_json: str) -> set[str]:
    """Extract object names from scene JSON. Returns empty set on unexpected shape."""
    try:
        data = json.loads(scene_json)
        objects = data.get("objects", [])
        return {obj["name"] for obj in objects if obj.get("name")}
    except (json.JSONDecodeError, AttributeError, TypeError):
        return set()


def _print_scene_diff(before: str, after: str) -> None:
    """Print added/removed object names between two scene snapshots."""
    names_before = _scene_object_names(before)
    names_after = _scene_object_names(after)
    added = sorted(names_after - names_before)
    removed = sorted(names_before - names_after)
    if not added and not removed:
        print("Diff: no object changes.", file=sys.stderr)
        return
    for name in added:
        print(f"  + {name}", file=sys.stderr)
    for name in removed:
        print(f"  - {name}", file=sys.stderr)
    print(f"Diff: +{len(added)} -{len(removed)} objects.", file=sys.stderr)


def _snapshot(host: str, port: int) -> str | None:
    """Return scene JSON snapshot, or None on connection failure."""
    try:
        return get_scene_info(host, port)
    except (ConnectionRefusedError, OSError) as exc:
        print(f"Warning: scene snapshot failed ({exc}).", file=sys.stderr)
        return None


# ── verbose / usage helper ────────────────────────────────────────────────────

def _print_usage(usage) -> None:
    """Print token usage stats including cache hit/miss to stderr."""
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    created = getattr(usage, "cache_creation_input_tokens", 0) or 0
    est_saved = int(cached * 0.9)
    print(
        f"Usage — in: {usage.input_tokens}  out: {usage.output_tokens}"
        f"  cache_hit: {cached}  cache_write: {created}  est_saved: ~{est_saved} tokens",
        file=sys.stderr,
    )


# ── Claude generation ─────────────────────────────────────────────────────────

def generate_blender_script(prompt: str, model: str, stream: bool = False, verbose: bool = False) -> str:
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
        if verbose:
            _print_usage(s.get_final_message().usage)
        return "".join(parts)

    response = client.messages.create(**kwargs)
    if verbose:
        _print_usage(response.usage)
    return response.content[0].text


def read_batch_prompts(path: str) -> list[str]:
    """Read non-empty, non-comment lines from a batch prompts file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


# ── iterate helper ────────────────────────────────────────────────────────────

def _execute_with_iterate(script: str, args, label: str = "") -> str:
    """Send script to Blender; on error ask Claude to fix, up to args.iterate times."""
    max_iter = args.iterate or 0
    current = script

    for attempt in range(max_iter + 1):
        tag = f" [{label}]" if label else ""
        print(f"Sending to Blender ({args.host}:{args.port}){tag}...", file=sys.stderr)
        try:
            ok, msg = _send_raw(current, args.host, args.port)
        except (ConnectionRefusedError, OSError):
            print(
                f"Error: Blender MCP not reachable on {args.host}:{args.port}.\n"
                "Start Blender, enable BlenderMCP add-on, click 'Connect to Claude'.",
                file=sys.stderr,
            )
            sys.exit(1)

        if ok:
            if msg:
                print(f"Blender: {msg}", file=sys.stderr)
            print("Done.", file=sys.stderr)
            return current

        if attempt >= max_iter:
            print(f"Blender error: {msg}", file=sys.stderr)
            sys.exit(1)

        print(f"  Error (attempt {attempt + 1}/{max_iter}): {msg}  — asking Claude to fix...", file=sys.stderr)
        repair = (
            f"Fix this bpy script that raised an error in Blender:\n\n"
            f"```python\n{current}\n```\n\n"
            f"Error: {msg}\n\n"
            f"Return only the corrected Python code."
        )
        current = generate_blender_script(repair, args.model, verbose=args.verbose)

    return current


# ── single-prompt pipeline ────────────────────────────────────────────────────

def run_single(prompt: str, args) -> None:
    if args.preset:
        prompt = PRESETS[args.preset] + prompt

    if args.scene:
        print("Fetching scene from Blender...", file=sys.stderr)
        try:
            scene_json = get_scene_info(args.host, args.port)
            prompt = f"Current Blender scene:\n{scene_json}\n\nTask: {prompt}"
        except (ConnectionRefusedError, OSError) as exc:
            print(f"Warning: cannot reach Blender MCP ({exc}). Ignoring --scene.", file=sys.stderr)

    script = generate_blender_script(prompt, args.model, stream=args.stream, verbose=args.verbose)

    if args.output:
        _write_file(args.output, script)
    elif not args.stream:
        print(script)

    if args.send:
        scene_before = _snapshot(args.host, args.port) if args.diff else None

        if args.iterate:
            script = _execute_with_iterate(script, args)
            if args.output:
                _write_file(args.output, script)  # overwrite with fixed version
        else:
            _send(script, args.host, args.port)

        if scene_before is not None:
            scene_after = _snapshot(args.host, args.port)
            if scene_after is not None:
                _print_scene_diff(scene_before, scene_after)


# ── batch pipeline ────────────────────────────────────────────────────────────

def run_batch(prompts: list[str], args) -> None:
    out_dir = Path(args.output_dir) if args.output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(args.batch).stem
    total = len(prompts)

    for i, prompt in enumerate(prompts, start=1):
        print(f"[{i}/{total}] {prompt[:60]}", file=sys.stderr)
        if args.preset:
            prompt = PRESETS[args.preset] + prompt
        script = generate_blender_script(prompt, args.model, verbose=args.verbose)
        out_path = out_dir / f"{stem}_{i:03d}.py"
        _write_file(str(out_path), script)

        if args.send:
            scene_before = _snapshot(args.host, args.port) if args.diff else None

            if args.iterate:
                script = _execute_with_iterate(script, args, label=f"{i}/{total}")
                _write_file(str(out_path), script)  # overwrite with fixed version
            else:
                _send(script, args.host, args.port)

            if scene_before is not None:
                scene_after = _snapshot(args.host, args.port)
                if scene_after is not None:
                    _print_scene_diff(scene_before, scene_after)


# ── watch pipeline ────────────────────────────────────────────────────────────

def run_watch(path: str, args) -> None:
    """Poll a prompt text file; regenerate (and optionally send) on each save."""
    p = Path(path)
    if not p.exists():
        print(f"Error: watch file not found: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Watching {path}  (Ctrl+C to stop)", file=sys.stderr)
    last_mtime = None

    try:
        while True:
            try:
                mtime = p.stat().st_mtime
            except OSError:
                time.sleep(0.5)
                continue

            if mtime != last_mtime:
                last_mtime = mtime
                prompt = p.read_text(encoding="utf-8").strip()
                if prompt:
                    print(f"\n--- {time.strftime('%H:%M:%S')} | {prompt[:60]} ---", file=sys.stderr)
                    run_single(prompt, args)

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nWatch stopped.", file=sys.stderr)


# ── shared helpers ────────────────────────────────────────────────────────────

def _write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {path}", file=sys.stderr)


def _send(script: str, host: str, port: int) -> None:
    """Send script to Blender (no iterate). Exits 1 on failure."""
    print(f"Sending to Blender ({host}:{port})...", file=sys.stderr)
    try:
        ok, msg = _send_raw(script, host, port)
    except (ConnectionRefusedError, OSError):
        print(
            f"Error: Blender MCP not reachable on {host}:{port}.\n"
            "Start Blender, enable BlenderMCP add-on, click 'Connect to Claude'.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not ok:
        print(f"Error: Blender execution failed: {msg}", file=sys.stderr)
        sys.exit(1)
    if msg:
        print(f"Blender: {msg}", file=sys.stderr)
    print("Done.", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude → Blender: natural language to bpy scripts"
    )

    # Mutually exclusive input modes
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("prompt", nargs="?", help="What to build in Blender")
    input_group.add_argument("--batch", metavar="FILE", help="File of prompts (one per line)")
    input_group.add_argument("--watch", metavar="FILE", help="Prompt text file to watch; regenerate on each save")

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
    parser.add_argument("--verbose", action="store_true", help="Print token usage (cache hit/miss) after each call")
    parser.add_argument(
        "--iterate", type=int, default=0, metavar="N",
        help="Auto-fix: if Blender reports an error, re-prompt Claude up to N times (requires --send)",
    )
    parser.add_argument("--diff", action="store_true", help="Show scene object diff before/after execution (requires --send)")
    parser.add_argument(
        "--preset", choices=list(PRESETS), metavar="STYLE",
        help=f"Style preset prepended to prompt ({', '.join(PRESETS)})",
    )

    args = parser.parse_args()

    if args.iterate and not args.send:
        parser.error("--iterate requires --send")
    if args.diff and not args.send:
        parser.error("--diff requires --send")

    if args.watch:
        run_watch(args.watch, args)
    elif args.batch:
        prompts = read_batch_prompts(args.batch)
        if not prompts:
            print("Error: batch file is empty.", file=sys.stderr)
            sys.exit(1)
        run_batch(prompts, args)
    else:
        run_single(args.prompt, args)


if __name__ == "__main__":
    main()
