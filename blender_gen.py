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
    python blender_gen.py "forest" --send --preview
    python blender_gen.py "add a torus" --auto-model --verbose       # → haiku
    python blender_gen.py --batch p.txt --history runs.jsonl         # replay log
    python blender_gen.py "neon city" --dry-run --auto-model         # plan only
    python blender_gen.py "forest" --cost --verbose                  # show spend
    python blender_gen.py --batch p.txt --cost-budget 0.25            # halt on budget
    python blender_gen.py "donut" --explain                          # add rationale
    python blender_gen.py --exec scenes/space_metaverse.py --preview  # run + render
    python blender_gen.py "cityscape" --theme themes.json --preset vaporwave
    python blender_gen.py "robot" --save-state runs.jsonl              # replay log
    python blender_gen.py "city" --theme-url https://example.com/themes.json --preset noir
    python blender_gen.py "tree" --retry 3                            # retry on flaky network
    python blender_gen.py --list-presets                              # discover styles + exit
    python blender_gen.py "spiral" --history log.jsonl --rate 5       # feed flywheel
    python blender_gen.py --list-demos                                # Space Metaverse catalog
    python blender_gen.py --demo earth --preview                      # one-liner demo
"""

import anthropic
import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 on stdout/stderr so help text and messages don't crash on Windows cp1252 consoles.
# reconfigure() is 3.7+; guard for older stdio wrappers that lack it.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001 — defensive: never crash on stream config
            pass

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
# Keys are lowercase. Extensible at runtime via --theme FILE.
PRESETS: dict[str, str] = {
    "cyberpunk": "Style: neon-lit cyberpunk aesthetic — glowing emissive materials in cyan/magenta/yellow, dark metallic surfaces, wet reflective ground, volumetric fog. ",
    "nature":    "Style: organic low-poly nature scene — earth tones, subsurface scattering on foliage, soft diffuse lighting, no sharp edges. ",
    "abstract":  "Style: abstract geometric art — bold primary colors, hard-edge materials, dramatic directional lighting, mathematical precision. ",
    "scifi":     "Style: hard-surface sci-fi — metallic panels with subtle emission, modular geometry, cool blue/white lighting, clean industrial aesthetic. ",
    "toon":      "Style: toon-shaded cartoon — flat colors with Toon BSDF, thick outlines via Solidify modifier, bright saturated palette, no cast shadows. ",
}

# One-liner demos — showcase the value proposition without composing 5 flags.
# Each maps NAME -> {scene: file, planet: earth|moon|mars|None, brief: KafCade mission line}
# planet=None means send as-is; otherwise patch PLANET constant before sending.
DEMOS: dict[str, dict] = {
    "earth":     {"scene": "scenes/space_metaverse.py", "planet": "earth",
                  "brief": "UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY TERRA"},
    "moon":      {"scene": "scenes/space_metaverse.py", "planet": "moon",
                  "brief": "UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY LUNA"},
    "mars":      {"scene": "scenes/space_metaverse.py", "planet": "mars",
                  "brief": "UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY ARES"},
    "cyberpunk": {"scene": "scenes/cyberpunk_city.py", "planet": None,
                  "brief": "UNIVERSE -> GALAXY SOL -> SYSTEM 3 -> BODY TERRA -> REGION NEO-KYOTO"},
}

# Bpy script sent to Blender to render a fast preview frame.
# {path!r} → repr()-escaped output path; camera added if scene has none.
RENDER_SCRIPT = """\
import bpy

if not bpy.context.scene.camera:
    bpy.ops.object.camera_add(location=(7.36, -6.93, 4.96), rotation=(1.11, 0.0, 0.81))
    bpy.context.scene.camera = bpy.context.object

scene = bpy.context.scene
scene.render.resolution_x = 480
scene.render.resolution_y = 270
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = {path!r}
bpy.ops.render.render(write_still=True)
"""

# Fixed preview path in user home — consistent across calls, easy to find.
PREVIEW_PATH = str(Path.home() / ".blender_gen_preview.png")

# Per-million-token USD rates: (input, output, cache_read, cache_write).
# Approximate public pricing pattern: cache_read ≈ 10% of input, cache_write ≈ 1.25× input, output ≈ 5× input.
# Update from anthropic.com/pricing when models change.
PRICING: dict[str, tuple] = {
    "claude-opus-4-7":            (15.00, 75.00, 1.50, 18.75),
    "claude-sonnet-4-6":          ( 3.00, 15.00, 0.30,  3.75),
    "claude-haiku-4-5-20251001":  ( 0.80,  4.00, 0.08,  1.00),
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


# ── preview helpers ───────────────────────────────────────────────────────────

def _open_preview(path: str) -> None:
    """Open image in the system default viewer. Cross-platform, no native extensions."""
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", path])
    elif system == "Windows":
        # os.startfile avoids shell=True; safer than subprocess(start, shell=True)
        os.startfile(path)  # noqa: S606 - Windows-only stdlib API
    else:
        subprocess.Popen(["xdg-open", path])


def _render_preview(host: str, port: int) -> None:
    """Render a 480×270 PNG preview in Blender and open it (localhost only)."""
    render_code = RENDER_SCRIPT.format(path=PREVIEW_PATH)
    print("Rendering preview...", file=sys.stderr)
    try:
        ok, msg = _send_raw(render_code, host, port)
    except (ConnectionRefusedError, OSError) as exc:
        print(f"Warning: preview render failed ({exc}).", file=sys.stderr)
        return
    if not ok:
        print(f"Warning: preview render error: {msg}", file=sys.stderr)
        return
    print(f"Preview: {PREVIEW_PATH}", file=sys.stderr)
    if host in ("localhost", "127.0.0.1"):
        _open_preview(PREVIEW_PATH)
    else:
        print(f"  (remote host — open {PREVIEW_PATH} on {host})", file=sys.stderr)


# ── history / auto-model helpers ──────────────────────────────────────────────

# Verbs that signal a small targeted edit rather than a full-scene build.
EDIT_VERBS = {"add", "remove", "delete", "move", "scale", "rotate", "set", "change",
              "rename", "color", "tint", "shift", "translate", "duplicate"}


def _pick_model(prompt: str, default: str) -> str:
    """Heuristic: short imperative edit → haiku; full-scene description → opus.
    Returns default if the prompt does not match either pattern."""
    words = prompt.strip().lower().split()
    if not words:
        return default
    if len(words) <= 8 and words[0] in EDIT_VERBS:
        return "claude-haiku-4-5-20251001"
    if len(words) > 20:
        return "claude-opus-4-7"
    return default


def _log_history(path: str, model: str, prompt: str, script: str, rating: int | None = None) -> None:
    """Append one JSONL record per generation. Safe to share across processes (append-mode).

    rating (1-5, optional) is the user's quality score — the SkillOpt training signal.
    Labeled prompt-script-rating tuples accumulate into a fine-tuning corpus over time."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model,
        "prompt": prompt,
        "script": script,
    }
    if rating is not None:
        record["rating"] = rating
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:
        print(f"Warning: history write failed ({exc}).", file=sys.stderr)


def _save_state(path: str, args, mode: str, target: str) -> None:
    """Append a JSONL record of this CLI invocation for replay.
    Strips falsy/default values to keep the log compact."""
    args_dict = {k: v for k, v in vars(args).items()
                 if v not in (None, False, 0, "") and k != "save_state"}
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "target": target,
        "args": args_dict,
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except OSError as exc:
        print(f"Warning: save-state write failed ({exc}).", file=sys.stderr)


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


def _estimate_cost(usage, model: str) -> float | None:
    """Return USD cost estimate for one call. None if model has no PRICING entry."""
    rates = PRICING.get(model)
    if rates is None:
        return None
    in_r, out_r, cr_r, cw_r = rates
    in_tok = (usage.input_tokens or 0)
    out_tok = (usage.output_tokens or 0)
    cr_tok = getattr(usage, "cache_read_input_tokens", 0) or 0
    cw_tok = getattr(usage, "cache_creation_input_tokens", 0) or 0
    # Anthropic billing: input_tokens excludes cache_read + cache_creation tokens (each priced separately).
    return (in_tok * in_r + out_tok * out_r + cr_tok * cr_r + cw_tok * cw_r) / 1_000_000


def _print_cost(usage, model: str) -> None:
    """Print one-line USD cost estimate to stderr."""
    cost = _estimate_cost(usage, model)
    if cost is None:
        print(f"Cost: unknown (no PRICING entry for {model})", file=sys.stderr)
        return
    print(f"Cost: ${cost:.4f}  (model={model})", file=sys.stderr)


# ── Claude generation ─────────────────────────────────────────────────────────

EXPLAIN_SUFFIX = (
    "\n\nAdditionally: prepend a Python comment block of the form\n"
    "# Design rationale:\n# <2-3 sentences explaining the approach, key choices, and trade-offs>\n"
    "before the import line."
)

# Transient errors → retry. Anything else (auth/bad-request/not-found) → raise.
# Resolved lazily to keep import side-effect-free if the SDK changes shape.
def _transient_errors() -> tuple:
    return (
        getattr(anthropic, "APIConnectionError", OSError),
        getattr(anthropic, "APITimeoutError", TimeoutError),
        getattr(anthropic, "RateLimitError", OSError),
        getattr(anthropic, "InternalServerError", OSError),
    )


def _call_with_retry(fn, retries: int):
    """Invoke fn() with up to `retries` exponential-backoff retries on transient API errors.
    Backoff: 1s, 2s, 4s, ... capped at 30s. retries=0 means single attempt (legacy behavior)."""
    if retries <= 0:
        return fn()
    transient = _transient_errors()
    for attempt in range(retries + 1):
        try:
            return fn()
        except transient as exc:
            if attempt >= retries:
                raise
            delay = min(2 ** attempt, 30)
            print(f"  Transient API error ({type(exc).__name__}): {exc} — retrying in {delay}s "
                  f"[{attempt + 1}/{retries}]", file=sys.stderr)
            time.sleep(delay)


def generate_blender_script(prompt: str, model: str, stream: bool = False, verbose: bool = False,
                             show_cost: bool = False, dry_run: bool = False,
                             explain: bool = False, cost_sink: list | None = None,
                             retries: int = 0) -> str:
    """Call Claude with a cached system prompt. Returns complete bpy script.

    dry_run=True skips the API call, prints the resolved model + prompt preview, returns "".
    cost_sink, if a list, has the per-call USD cost appended (None-safe entries skipped).
    """
    if explain:
        prompt = prompt + EXPLAIN_SUFFIX

    if dry_run:
        preview = prompt if len(prompt) <= 240 else prompt[:240] + "…"
        print(f"[DRY RUN] model={model}", file=sys.stderr)
        print(f"[DRY RUN] prompt={preview}", file=sys.stderr)
        return ""

    client = anthropic.Anthropic()

    kwargs = dict(
        model=model,
        max_tokens=4096,
        system=SYSTEM_BLOCK,
        messages=[{"role": "user", "content": prompt}],
    )

    def _post(usage):
        if verbose:
            _print_usage(usage)
        if show_cost:
            _print_cost(usage, model)
        if cost_sink is not None:
            c = _estimate_cost(usage, model)
            if c is not None:
                cost_sink.append(c)

    if stream:
        def _do_stream():
            parts = []
            with client.messages.stream(**kwargs) as s:
                for text in s.text_stream:
                    print(text, end="", flush=True)
                    parts.append(text)
            print()
            return parts, s.get_final_message().usage
        parts, usage = _call_with_retry(_do_stream, retries)
        _post(usage)
        return "".join(parts)

    response = _call_with_retry(lambda: client.messages.create(**kwargs), retries)
    _post(response.usage)
    return response.content[0].text


def read_batch_prompts(path: str) -> list[str]:
    """Read non-empty, non-comment lines from a batch prompts file."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def load_theme_file(path: str) -> dict:
    """Load a JSON file of {style_name: tokens} and lowercase the keys.
    Exits with a clear error on bad JSON or wrong shape (boundary input, not internal)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: cannot load --theme {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(f"Error: --theme file must be a JSON object, got {type(data).__name__}.", file=sys.stderr)
        sys.exit(1)
    return {str(k).lower(): str(v) for k, v in data.items()}


THEME_CACHE_DIR = Path.home() / ".blender_gen_themes"
THEME_URL_TIMEOUT = 10  # seconds


def fetch_theme_url(url: str) -> dict:
    """Download a theme JSON over http(s), cache by URL hash, return parsed dict.
    Restricts scheme to http/https to avoid file:// and other smuggled URLs."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        print(f"Error: --theme-url scheme must be http or https, got {parsed.scheme!r}.", file=sys.stderr)
        sys.exit(1)

    THEME_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(url.encode()).hexdigest()[:16]
    cache_path = THEME_CACHE_DIR / f"{cache_key}.json"

    if cache_path.exists():
        print(f"Theme cache hit: {cache_path.name}", file=sys.stderr)
        return load_theme_file(str(cache_path))

    print(f"Fetching theme from {url}...", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "claude-blender/0.14"})
    try:
        with urllib.request.urlopen(req, timeout=THEME_URL_TIMEOUT) as resp:  # noqa: S310 - scheme validated above
            data = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"Error: --theme-url fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)

    cache_path.write_bytes(data)
    print(f"Theme cached: {cache_path}", file=sys.stderr)
    return load_theme_file(str(cache_path))


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

    model = _pick_model(prompt, args.model) if args.auto_model else args.model
    if args.auto_model and (args.verbose or args.dry_run):
        print(f"auto-model: {model}", file=sys.stderr)

    script = generate_blender_script(
        prompt, model,
        stream=args.stream, verbose=args.verbose,
        show_cost=args.cost, dry_run=args.dry_run,
        explain=args.explain, retries=args.retry,
    )

    if not script:  # dry-run path; nothing downstream applies
        return

    if args.history:
        _log_history(args.history, model, prompt, script, rating=args.rate)

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

        if args.preview:
            _render_preview(args.host, args.port)


# ── batch pipeline ────────────────────────────────────────────────────────────

def run_batch(prompts: list[str], args) -> None:
    out_dir = Path(args.output_dir) if args.output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(args.batch).stem
    total = len(prompts)
    cost_sink: list = [] if args.cost_budget is not None else None

    for i, prompt in enumerate(prompts, start=1):
        print(f"[{i}/{total}] {prompt[:60]}", file=sys.stderr)
        if args.preset:
            prompt = PRESETS[args.preset] + prompt
        model = _pick_model(prompt, args.model) if args.auto_model else args.model
        if args.auto_model and (args.verbose or args.dry_run):
            print(f"  auto-model: {model}", file=sys.stderr)
        script = generate_blender_script(
            prompt, model,
            verbose=args.verbose, show_cost=args.cost, dry_run=args.dry_run,
            explain=args.explain, cost_sink=cost_sink, retries=args.retry,
        )

        # Budget gate: halt before next call once cumulative spend exceeds threshold
        if cost_sink is not None and args.cost_budget is not None:
            spent = sum(cost_sink)
            if spent > args.cost_budget:
                print(f"Cost budget ${args.cost_budget:.4f} exceeded "
                      f"(cumulative ${spent:.4f} after {i} call(s)). Halting batch.",
                      file=sys.stderr)
                break

        if not script:  # dry-run; skip file write + downstream
            continue
        out_path = out_dir / f"{stem}_{i:03d}.py"
        _write_file(str(out_path), script)

        if args.history:
            _log_history(args.history, model, prompt, script, rating=args.rate)

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

            if args.preview:
                _render_preview(args.host, args.port)


# ── exec pipeline ─────────────────────────────────────────────────────────────

def run_exec(path: str, args) -> None:
    """Send a .py file to Blender as-is (no Claude call). Composable with --diff/--preview/--iterate."""
    p = Path(path)
    if not p.exists():
        print(f"Error: --exec file not found: {path}", file=sys.stderr)
        sys.exit(1)

    script = p.read_text(encoding="utf-8")
    print(f"Loaded {path} ({len(script)} chars).", file=sys.stderr)

    scene_before = _snapshot(args.host, args.port) if args.diff else None

    if args.iterate:
        script = _execute_with_iterate(script, args)
    else:
        _send(script, args.host, args.port)

    if scene_before is not None:
        scene_after = _snapshot(args.host, args.port)
        if scene_after is not None:
            _print_scene_diff(scene_before, scene_after)

    if args.preview:
        _render_preview(args.host, args.port)


# ── demo pipeline ─────────────────────────────────────────────────────────────

def _print_mission_brief(name: str, cfg: dict) -> None:
    """Print a KafCade mission-brief header — CLI echo of the Kimi HUD."""
    print(f"\n{'═' * 60}", file=sys.stderr)
    print(f" SPACE METAVERSE · DEMO: {name.upper()}", file=sys.stderr)
    print(f" {cfg['brief']}", file=sys.stderr)
    print(f" scene: {cfg['scene']}", file=sys.stderr)
    print(f"{'═' * 60}\n", file=sys.stderr)


def run_demo(name: str, args) -> None:
    """Send one of the built-in demo scenes to Blender. Patches PLANET at runtime for space demos."""
    if name not in DEMOS:
        print(f"Error: unknown demo {name!r}. Available: {', '.join(sorted(DEMOS))}", file=sys.stderr)
        sys.exit(1)

    cfg = DEMOS[name]
    scene_path = Path(cfg["scene"])
    if not scene_path.exists():
        print(f"Error: demo scene not found: {scene_path}", file=sys.stderr)
        sys.exit(1)

    _print_mission_brief(name, cfg)

    script = scene_path.read_text(encoding="utf-8")

    # Patch PLANET constant for space_metaverse variants — no file edit, in-memory only
    if cfg["planet"]:
        import re  # noqa: PLC0415 — local import, only used by demo path
        script = re.sub(
            r'^PLANET\s*=\s*"[^"]*"',
            f'PLANET = "{cfg["planet"]}"',
            script,
            count=1,
            flags=re.MULTILINE,
        )

    scene_before = _snapshot(args.host, args.port) if args.diff else None

    if args.iterate:
        script = _execute_with_iterate(script, args)
    else:
        _send(script, args.host, args.port)

    if scene_before is not None:
        scene_after = _snapshot(args.host, args.port)
        if scene_after is not None:
            _print_scene_diff(scene_before, scene_after)

    if args.preview:
        _render_preview(args.host, args.port)


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
        description="Claude -> Blender: natural language to bpy scripts"
    )

    # Input modes are mutually exclusive but not always required
    # (--list-presets exits before any input is needed).
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("prompt", nargs="?", help="What to build in Blender")
    input_group.add_argument("--batch", metavar="FILE", help="File of prompts (one per line)")
    input_group.add_argument("--watch", metavar="FILE", help="Prompt text file to watch; regenerate on each save")
    input_group.add_argument("--exec", dest="exec_path", metavar="FILE",
                              help="Execute a .py file in Blender as-is (no Claude call); requires running BlenderMCP")
    input_group.add_argument("--demo", metavar="NAME",
                              help="Run a built-in Space Metaverse demo scene (list: --list-demos)")

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
    parser.add_argument(
        "--retry", type=int, default=0, metavar="N",
        help="Retry the API call on transient errors (connection, timeout, 429, 5xx) with exponential backoff",
    )
    parser.add_argument("--diff", action="store_true", help="Show scene object diff before/after execution (requires --send)")
    parser.add_argument("--preview", action="store_true", help="Render a 480x270 preview after execution and open it (requires --send)")
    parser.add_argument(
        "--preset", metavar="STYLE",
        help=f"Style preset prepended to prompt (built-in: {', '.join(PRESETS)}; extend via --theme)",
    )
    parser.add_argument(
        "--theme", metavar="FILE",
        help="JSON file {name: tokens} merged into PRESETS at startup; use with --preset NAME",
    )
    parser.add_argument(
        "--theme-url", metavar="URL",
        help="HTTPS URL of a JSON theme; cached to ~/.blender_gen_themes/; merges into PRESETS",
    )
    parser.add_argument(
        "--save-state", metavar="FILE",
        help="Append a JSONL replay record (mode, target, args) after this invocation",
    )
    parser.add_argument(
        "--list-presets", action="store_true",
        help="Print all available styles (built-in + --theme + --theme-url) and exit",
    )
    parser.add_argument(
        "--list-demos", action="store_true",
        help="Print all built-in demo scenes with mission-brief lines and exit",
    )
    parser.add_argument(
        "--rate", type=int, metavar="N", default=None,
        help="Rating 1-5 for the last generation; appended to --history JSONL as {rating: N} "
             "(requires --history; enables the SkillOpt training-data flywheel)",
    )
    parser.add_argument(
        "--history", metavar="FILE",
        help="Append JSONL {ts, model, prompt, script} record after each generation",
    )
    parser.add_argument(
        "--auto-model", action="store_true",
        help="Route by prompt: short edits (<=8 words + edit verb) -> haiku; long (>20 words) -> opus",
    )
    parser.add_argument(
        "--cost", action="store_true",
        help="Print USD cost estimate after each Claude call (uses PRICING table)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip the API call; print resolved model + prompt preview only",
    )
    parser.add_argument(
        "--cost-budget", type=float, metavar="USD", default=None,
        help="Halt batch run once cumulative cost exceeds USD threshold (batch only)",
    )
    parser.add_argument(
        "--explain", action="store_true",
        help="Ask Claude to prepend a '# Design rationale:' comment block to the script",
    )

    args = parser.parse_args()

    if args.exec_path or args.demo:
        args.send = True  # --exec/--demo are meaningless without sending; must precede --send guards

    if args.iterate and not args.send:
        parser.error("--iterate requires --send")
    if args.diff and not args.send:
        parser.error("--diff requires --send")
    if args.preview and not args.send:
        parser.error("--preview requires --send")
    if args.cost_budget is not None and not args.batch:
        parser.error("--cost-budget requires --batch")

    if args.theme:
        PRESETS.update(load_theme_file(args.theme))
    if args.theme_url:
        PRESETS.update(fetch_theme_url(args.theme_url))

    if args.list_presets:
        for name in sorted(PRESETS):
            tokens = PRESETS[name].strip()
            preview = tokens if len(tokens) <= 80 else tokens[:77] + "..."
            print(f"  {name:<12}  {preview}")
        return

    if args.list_demos:
        print("Available Space Metaverse demos (each requires --send + running BlenderMCP):\n")
        for name in sorted(DEMOS):
            cfg = DEMOS[name]
            print(f"  {name:<12}  {cfg['brief']}")
            print(f"  {'':<12}  scene: {cfg['scene']}\n")
        return

    if args.rate is not None:
        if not 1 <= args.rate <= 5:
            parser.error(f"--rate must be 1-5, got {args.rate}")
        if not args.history:
            parser.error("--rate requires --history (rating attaches to the log record)")

    if args.preset and args.preset not in PRESETS:
        parser.error(f"--preset {args.preset!r} not in available styles: {', '.join(PRESETS)}")

    if not (args.prompt or args.batch or args.watch or args.exec_path or args.demo):
        parser.error("one of the arguments prompt --batch --watch --exec --demo is required")

    if args.demo:
        run_demo(args.demo, args)
        mode, target = "demo", args.demo
    elif args.exec_path:
        run_exec(args.exec_path, args)
        mode, target = "exec", args.exec_path
    elif args.watch:
        run_watch(args.watch, args)
        mode, target = "watch", args.watch
    elif args.batch:
        prompts = read_batch_prompts(args.batch)
        if not prompts:
            print("Error: batch file is empty.", file=sys.stderr)
            sys.exit(1)
        run_batch(prompts, args)
        mode, target = "batch", args.batch
    else:
        run_single(args.prompt, args)
        mode, target = "single", args.prompt

    if args.save_state:
        _save_state(args.save_state, args, mode, target)


if __name__ == "__main__":
    main()
