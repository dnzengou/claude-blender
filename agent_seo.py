"""
agent_seo — portable agent-detectable SEO scaffolder.

Drop this single file into any project and get a reproducible way to emit the
four files that make a codebase legible to AI agents and LLM crawlers:

    llms.txt                 (llmstxt.org index)
    llms-full.txt            (full concatenated context)
    AGENTS.md                (agents.md convention)
    .well-known/agents.json  (self-describing capability manifest)

Zero dependencies. Pure stdlib. ARM-compatible. MIT.

Usage (library):
    from agent_seo import AgentManifest, Capability, write_all
    m = AgentManifest(
        name="my-tool",
        human="My Tool",
        summary="One sentence on what it does.",
        repository="https://github.com/me/my-tool",
        entry_point="my_tool.py",
        language="python",
        capabilities=[Capability(id="hello", summary="Say hello.",
                                  command="my-tool hello --name NAME")],
    )
    write_all(m, out_dir=".")

Usage (CLI):
    python agent_seo.py --init           # scaffold a manifest.py next to you
    python agent_seo.py manifest.py .    # regenerate SEO files into cwd
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

__version__ = "0.1.0"


@dataclass
class Capability:
    id: str
    summary: str
    command: str
    requires: list[str] = field(default_factory=list)


@dataclass
class AgentManifest:
    name: str                   # machine name, kebab or snake
    human: str                  # human name
    summary: str                # one-sentence pitch
    repository: str
    entry_point: str
    language: str = "python"
    min_version: str = "3.9"
    dependencies: list[str] = field(default_factory=list)
    native_extensions: bool = False
    architectures: list[str] = field(default_factory=lambda: ["aarch64", "x86_64"])
    platforms: list[str] = field(default_factory=lambda: ["linux", "macos", "windows"])
    license: str = "MIT"
    contact_email: str = ""
    homepage: str = ""
    logo_url: str = ""
    legal_info_url: str = ""
    capabilities: list[Capability] = field(default_factory=list)
    docs: dict[str, str] = field(default_factory=dict)       # title -> relative path
    code: dict[str, str] = field(default_factory=dict)       # title -> relative path
    keywords: list[str] = field(default_factory=list)
    allow_training: bool = True
    citation_required: bool = False
    citation_file: str = ""
    api_key_env_var: str = ""
    network: str = ""
    dangerous_capabilities: list[str] = field(default_factory=list)

    @property
    def homepage_or_repo(self) -> str:
        return self.homepage or f"{self.repository}#readme"


# ── emitters ──────────────────────────────────────────────────────────────────

def render_agents_json(m: AgentManifest) -> str:
    """Produce the .well-known/agents.json payload."""
    payload = {
        "schema_version": "v1",
        "name_for_model": m.name.replace("-", "_"),
        "name_for_human": m.human,
        "description_for_human": m.summary,
        "description_for_model": m.summary,
        "repository": m.repository,
        "homepage": m.homepage_or_repo,
        "license": m.license,
        "logo_url": m.logo_url,
        "contact_email": m.contact_email,
        "legal_info_url": m.legal_info_url or f"{m.repository}/blob/main/LICENSE",
        "entry_point": m.entry_point,
        "runtime": {
            "language": m.language,
            "min_version": m.min_version,
            "dependencies": m.dependencies,
            "native_extensions": m.native_extensions,
            "architectures": m.architectures,
            "platforms": m.platforms,
        },
        "capabilities": [asdict(c) for c in m.capabilities],
        "ai_training_policy": {
            "allow_training": m.allow_training,
            "citation_required": m.citation_required,
            "citation_file": m.citation_file,
        },
        "security": {
            "api_key_env_var": m.api_key_env_var,
            "network": m.network,
            "dangerous_capabilities": m.dangerous_capabilities,
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def render_llms_txt(m: AgentManifest) -> str:
    """Produce the llmstxt.org index."""
    out: list[str] = [f"# {m.name}", "", f"> {m.summary}", ""]
    if m.docs:
        out += ["## Docs", ""]
        out += [f"- [{title}]({path})" for title, path in m.docs.items()]
        out.append("")
    if m.code:
        out += ["## Code", ""]
        out += [f"- [{title}]({path})" for title, path in m.code.items()]
        out.append("")
    out += ["## Manifest", "",
            "- [.well-known/agents.json](./.well-known/agents.json): machine-readable capability manifest",
            ""]
    return "\n".join(out)


def render_llms_full_txt(m: AgentManifest) -> str:
    """Produce the full concatenated context for LLM ingestion."""
    lines: list[str] = [f"# {m.name} — Full Context for LLM Ingestion", "",
                        m.summary, ""]
    lines += ["## Capabilities", ""]
    for c in m.capabilities:
        lines.append(f"- **{c.id}** — {c.summary}")
        lines.append(f"  - `{c.command}`")
        if c.requires:
            lines.append(f"  - requires: {', '.join(c.requires)}")
    lines += ["", "## Install", "",
              "```bash",
              f"pip install {m.name}" if m.language == "python" else f"# {m.name}",
              "```", ""]
    lines += ["## Repository", "", m.repository, "", "## License", "", m.license, ""]
    if m.keywords:
        lines += ["## Keywords", "", ", ".join(m.keywords), ""]
    return "\n".join(lines)


def render_agents_md(m: AgentManifest) -> str:
    """Produce an AGENTS.md scaffold."""
    out = ["# AGENTS.md", "",
           f"Conventions for AI coding agents working in **{m.name}**. "
           f"Follows the [AGENTS.md convention](https://agents.md/).",
           "",
           "## What this repo is", "",
           m.summary, "",
           f"- **Entry point:** `{m.entry_point}`",
           f"- **Language:** {m.language} {m.min_version}+",
           f"- **Dependencies:** {', '.join(m.dependencies) or 'stdlib only'}",
           f"- **Native extensions:** {'yes' if m.native_extensions else 'no (ARM-compatible)'}",
           ""]
    if m.capabilities:
        out += ["## Capabilities", ""]
        for c in m.capabilities:
            out.append(f"- `{c.command}` — {c.summary}")
        out.append("")
    out += ["## Conventions", "",
            "- Stdlib first; adding a dependency is a conversation.",
            "- Pure portable code; keep it ARM-compatible.",
            "- Validate at boundaries; trust internal code.",
            "- No comments explaining what the code does — only non-obvious why.",
            ""]
    return "\n".join(out)


def write_all(m: AgentManifest, out_dir: str | Path = ".") -> list[Path]:
    """Emit all four files into out_dir. Returns the list of written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".well-known").mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rel, body in [
        ("llms.txt",                 render_llms_txt(m)),
        ("llms-full.txt",            render_llms_full_txt(m)),
        ("AGENTS.md",                render_agents_md(m)),
        (".well-known/agents.json",  render_agents_json(m)),
    ]:
        p = out / rel
        p.write_text(body, encoding="utf-8")
        written.append(p)
    return written


# ── CLI ───────────────────────────────────────────────────────────────────────

_TEMPLATE = '''\
"""Edit this file, then run:  python agent_seo.py manifest.py ."""
from agent_seo import AgentManifest, Capability

MANIFEST = AgentManifest(
    name="my-tool",
    human="My Tool",
    summary="One sentence on what this tool does.",
    repository="https://github.com/me/my-tool",
    entry_point="my_tool.py",
    language="python",
    dependencies=[],
    keywords=["cli", "agents", "llms.txt"],
    api_key_env_var="",
    contact_email="",
    capabilities=[
        Capability(id="hello", summary="Say hello.",
                   command="my-tool hello --name NAME"),
    ],
    docs={"README": "./README.md"},
    code={"Entry point": "./my_tool.py"},
)
'''


def _load_manifest(path: str) -> AgentManifest:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_agent_seo_manifest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load manifest from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = getattr(mod, "MANIFEST", None)
    if m is None or type(m).__name__ != "AgentManifest":
        raise RuntimeError(f"{path} must expose MANIFEST: AgentManifest")
    return m


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="agent_seo — emit llms.txt + AGENTS.md + .well-known/agents.json from a manifest.",
    )
    ap.add_argument("--version", action="version", version=f"agent_seo {__version__}")
    ap.add_argument("--init", action="store_true",
                    help="Write a manifest.py template next to you and exit")
    ap.add_argument("manifest", nargs="?", help="Path to a Python file exposing MANIFEST: AgentManifest")
    ap.add_argument("out_dir", nargs="?", default=".", help="Output directory (default: .)")
    args = ap.parse_args(argv)

    if args.init:
        p = Path("manifest.py")
        if p.exists():
            print(f"refusing to overwrite {p} — delete it first", file=sys.stderr)
            return 1
        p.write_text(_TEMPLATE, encoding="utf-8")
        print(f"wrote {p} — edit it, then rerun: python agent_seo.py {p} .")
        return 0

    if not args.manifest:
        ap.error("provide a manifest path, or use --init")

    m = _load_manifest(args.manifest)
    written = write_all(m, args.out_dir)
    for p in written:
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
