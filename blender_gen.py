"""
Generate Blender Python scripts from natural language via Claude API.
ARM-optimized: pure Python, zero native extensions.

Usage:
    python blender_gen.py "spinning torus with gold material"
    python blender_gen.py "procedural city grid 10x10" -o city.py
    python blender_gen.py "solar system with orbits" --model claude-haiku-4-5-20251001
"""

import anthropic
import argparse
import sys

SYSTEM_PROMPT = """You are a Blender Python scripting expert. Output complete, runnable bpy scripts only.
Rules:
- Start every script with: import bpy
- Clear existing scene objects when starting fresh: bpy.ops.wm.read_factory_settings(use_empty=True)
- Use only: bpy.data, bpy.ops, bpy.context — no external imports
- Scripts must run in Blender's Text Editor (Run Script button) or bpy.exec_expression
- Default to low-poly geometry unless the user specifies detail
- No placeholder comments like "# add more objects here" — complete the implementation
- Return ONLY the Python code, no prose, no markdown fences"""


def generate_blender_script(prompt: str, model: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(
        description="Claude → Blender: generate bpy scripts from natural language"
    )
    parser.add_argument("prompt", help="What to build in Blender")
    parser.add_argument(
        "--model",
        default="claude-opus-4-7",
        choices=["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        help="Claude model (default: opus-4-7 for best code quality)",
    )
    parser.add_argument(
        "--output", "-o", metavar="FILE", help="Write script to file instead of stdout"
    )
    args = parser.parse_args()

    script = generate_blender_script(args.prompt, args.model)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"Saved: {args.output}", file=sys.stderr)
    else:
        print(script)


if __name__ == "__main__":
    main()
