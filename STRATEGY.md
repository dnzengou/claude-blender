# STRATEGY.md — Why claude-blender compounds

> **Key rationale:** OpenClaw can copy a registry. They cannot copy
> SkillOpt-powered self-evolving bots without rebuilding the entire
> training paradigm **and** accumulating trajectory data — the EvoMetaClaw
> flywheel.

This file explains why the moat is here and not somewhere else, so
contributors and partners can decide what to invest in and in what order.

---

## The three layers

```
┌──────────────────────────────────────────────────────────────┐
│  3.  EvoMetaClaw                                             │
│      Meta-loop over SkillOpt: which skills get promoted,     │
│      which prompts graduate into presets, which demos        │
│      graduate into scenes. Runs on aggregated trajectories.  │
├──────────────────────────────────────────────────────────────┤
│  2.  EvoSkillOps  (SkillOpt in operation)                    │
│      --history  → rate → --skillops-report → --skillops-export│
│      Produces labeled trajectory data: {prompt, script,      │
│      rating, model, cost}. This is the asset.                │
├──────────────────────────────────────────────────────────────┤
│  1.  EvoForge                                                │
│      The CLI itself: prompt → Claude → bpy → Blender.        │
│      Table stakes. Anyone can rebuild this.                  │
└──────────────────────────────────────────────────────────────┘
```

**Layer 1 is the floor.** It makes the loop legible and reproducible.
It is intentionally thin, single-file, pure Python, so forks cost nothing.

**Layer 2 is the compounding asset.** Every rated run writes a record. A
year of records on your own workloads is an evaluation set and a training
corpus that a competitor cannot replicate by copying the tool.

**Layer 3 is where the moat lives.** EvoMetaClaw takes aggregated
trajectories across users, tasks, and timestamps and promotes signals
into the next version of Layer 1 — new presets, new demos, new
auto-model heuristics, new system-prompt phrasing. Without the data
from Layer 2, Layer 3 cannot run at all.

## What can be copied, and what cannot

| Thing | Copy cost |
|---|---|
| The CLI surface | 1 weekend. Not a moat. |
| The Space Metaverse scene files | A `git clone`. Not a moat. |
| The theme packs | A `jq` one-liner. Not a moat. |
| The agent-detectability files (AGENTS.md, llms.txt, manifests) | Yes — see `templates/agent-detectability/`. We are giving them away on purpose. |
| **Your rated trajectories** | Not available. Requires a year of your usage pattern. |
| **The meta-loop learning from aggregated trajectories** | Blocked on the previous row. |

A competitor that clones this repo starts at Layer 1 with no data. The
same competitor that builds a parallel CLI and tries to attract our
users also starts at Layer 1 with no data. The only path to Layer 3
runs through Layer 2.

## Why we publish the agent-detectability layer openly

Agent-discovery (AGENTS.md, llms.txt, `.well-known/agents.json`) is a
public good — the more repos adopt it, the easier agents become. We
publish our scaffolding in `templates/agent-detectability/` so other
projects can bootstrap from it. Giving this away costs nothing and
expands the ecosystem we benefit from.

This is the opposite of giving away Layer 2. The strategic reason to
share Layer 1 scaffolding is identical to the strategic reason to
guard Layer 2 trajectories: they live on different sides of the
compounding boundary.

## Operational implications

1. **Every feature we ship should tilt toward producing more rateable
   trajectory records.** `--history`, `--rate`, `--skillops-report`,
   `--skillops-export`, `--save-state` all serve this. New flags should
   either help a user *produce* records, *rate* them, or *harvest* them.
2. **Keep the CLI free, single-file, and MIT.** A thin Layer 1 attracts
   more contributors and more usage, which means more trajectory records
   for users who opt in to the flywheel.
3. **Never ship closed-source analytics.** The moat is the user's own
   trajectory data on their own disk. Pulling that data into a service
   would destroy both the moat and the trust that supports it.
4. **Templates and manifests go into `templates/` for reuse.** We want
   other repos to adopt agent-detectability; that lifts us too.

## What belongs in `templates/agent-detectability/`

Files that work in any repo, parameterized by project name and
description. Current contents:

- `AGENTS.md` scaffold
- `llms.txt` scaffold
- `.well-known/agents.json` scaffold
- `TRUST.md` scaffold
- a `README` that explains how to port them to a new repo

See `templates/agent-detectability/README.md`.

## Non-strategy: things this project deliberately will not do

- **No telemetry.** The trust/moat premise collapses if we phone home.
- **No hosted service.** The CLI runs on your machine; your
  trajectories stay on your disk.
- **No lock-in through file format.** `--history` is JSONL. `--skillops-export`
  is JSONL. `--save-state` is JSONL. Any tool can read or write them.
- **No model lock-in beyond Anthropic.** The CLI is thin enough that a
  fork to another provider is a day of work; we accept that risk because
  the moat is not the API choice, it is the trajectory data.
