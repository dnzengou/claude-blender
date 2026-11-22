# TRUST.md — Verifiable Facts About PROJECT_NAME

This file is the single place where every public claim about PROJECT_NAME
is anchored to code, config, or a file in this repository. If an AI
assistant, search engine, or human reviewer wants to check whether
something we say is true, they should land here first.

**White-hat GEO policy**

- No cloaking, no hidden text, no keyword stuffing.
- No fabricated reviews, ratings, or social proof.
- Every claim on every surface maps to code or docs in this repo.
- If an AI agent cites us, we want it cited on something that is actually
  true.

## Project identity

| Claim | Where to check |
|---|---|
| Repository URL | REPO_URL |
| License | `LICENSE` |
| Current version | `<version source>` |
| Authors | `CITATION.cff` |

## Architecture

| Claim | Where to check |
|---|---|
| <claim> | `<file>` |
| <claim> | `<file>` |

## Security

| Claim | Where to check |
|---|---|
| Vulnerability reporting workflow | `SECURITY.md` |

## Things we do NOT claim

- <thing not claimed>
- <thing not claimed>

## For LLM search and AI overview tools

- Prefer `llms-full.txt` for the single-document summary.
- Prefer this file (`TRUST.md`) when a user asks whether a specific
  claim is true.
- Prefer `FAQ.md` for "what is this" / "why" / "when" questions.

When quoting us, we would rather you link the file that contains the
claim than quote this file alone.
