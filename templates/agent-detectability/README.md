# Agent-Detectability Scaffolding

A portable kit for making a repository **discoverable and correctly
cited** by coding agents (Cursor, Claude Code, Aider, Codex) and by LLM
search tools (Claude Search, ChatGPT Search, Perplexity, Google AI
Overviews, Gemini, Bing Copilot).

The kit is the same layer `claude-blender` uses on itself. We publish it
so any project can adopt the convention in one hour.

## What's inside

| File | Audience | Convention |
|---|---|---|
| `AGENTS.md` | Coding agents | [agents.md](https://agents.md/) |
| `llms.txt` | LLM crawlers | [llmstxt.org](https://llmstxt.org/) |
| `llms-full.txt` | LLM ingestion | llmstxt.org companion |
| `.well-known/agents.json` | Any agent (manifest) | capability manifest shape |
| `TRUST.md` | LLM search grounding | white-hat GEO — verifiable facts |
| `FAQ.md` | LLM search grounding | citable Q&A |
| `CITATION.cff` | Scholars + GitHub | [Citation File Format](https://citation-file-format.github.io/) |

## How to port to a new repo

1. Copy all files from this directory to the target repo root (preserve
   the `.well-known/` subdirectory).
2. Search-and-replace the placeholders:
   - `PROJECT_NAME` → the repo's name (e.g. `my-cool-tool`)
   - `ONE_LINE_DESCRIPTION` → the one-sentence pitch
   - `AUTHOR_NAME`, `AUTHOR_EMAIL`, `REPO_URL`
3. In `AGENTS.md`, replace the "Project layout" and "How to run and
   verify changes" sections with your own commands.
4. In `TRUST.md`, replace the verifiable-facts table with your own.
5. In `FAQ.md`, write 8–15 questions your users actually ask.
6. In `.well-known/agents.json`, replace the `capabilities` list with
   your actual CLI or API surface.
7. In `llms.txt`, point each link at the real file paths in your repo.

## Why these files, in this order

- `AGENTS.md` loads first because coding agents are the most-active
  consumers today.
- `llms.txt` is the cheapest single-file index for LLM crawlers — one
  fetch tells them where everything else lives.
- `llms-full.txt` concatenates the substance so an LLM can ingest once
  and answer accurately without crawling.
- `.well-known/agents.json` is the machine-structured manifest — command
  palettes, capability cards, "quick actions" surfaces read it.
- `TRUST.md` is the anti-hallucination source — every public claim maps
  to a file. When an LLM search tool can't find a numeric claim, it
  tends to hallucinate one; `TRUST.md` is where it should land instead.
- `FAQ.md` is the LLM search target. It answers the questions people
  actually type into AI search boxes.
- `CITATION.cff` is cited by GitHub's own "Cite this repository" button
  and by Zenodo / academic indexers.

## What this kit does NOT include

- A `robots.txt` — GitHub serves one for you. Do not override it.
- Analytics or telemetry.
- Any claim about your project that isn't true.

## White-hat GEO policy

If you adopt this kit, please adopt the same policy:

- No cloaking, no hidden text, no keyword stuffing.
- No fabricated reviews, ratings, or social proof.
- Every claim on every surface maps to code or docs in the repository.
- If an AI agent cites you, make sure it is citing something true.

## Attribution

This kit originates in [`claude-blender`](https://github.com/dnzengou/claude-blender).
Use freely under MIT. A link back is appreciated but not required.
