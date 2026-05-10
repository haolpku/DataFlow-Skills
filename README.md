# DataFlow-Skills (branch `v2`)

> **Branch scope.** This branch contains **a single skill**, `dataflow-pipeline-v2/`, the construction-time skill used by `DF-Agent (v2)` in the EMNLP evaluation. The full multi-module suite (operator builder, prompt-template builder, dev-context, etc.) lives on the `main` branch.
>
> 中文版本：[README_zh.md](./README_zh.md)

## What this skill does

`dataflow-pipeline-v2` guides a code agent (Claude Code, Cursor, etc.) to build a **DataFlow pipeline** from:

1. a JSONL sample path, and
2. a natural-language goal ("clean and score these reviews", "generate multi-hop QA from these chunks", etc.).

The output is a **stored pipeline object** that appears in the DataFlow-WebUI DAG editor and runs via the WebUI Run button. The agent never executes the pipeline itself.

## Why a v2 rewrite

The v1 of this skill (on `main`) was reasoning-style: it told the agent to "select appropriate operators from preferred primitives" and listed six core ops as starting points. In our evaluation we observed eight recurring failure modes:

1. agents called `list_operators` with no `category` argument and overflowed context with the full ~145-operator catalog;
2. agents treated `PromptedGenerator` as a universal first choice, mis-routing tasks that had a specialized operator (e.g. `Text2MultiHopQAGenerator` for multi-hop QA);
3. the v1 "always use KBC trio" rule fired in API-only environments where KBC operators are not installed;
4. agents picked `SFTGeneratorSeed` for fresh QA generation (the seed-generator requires already-existing SFT samples);
5. agents called `create_pipeline` mid-reasoning, pushing several incompatible drafts into the editor in one turn;
6. agents passed `llm_serving={"id": "..."}` (dict) instead of the bare string id;
7. agents passed `prompt_template={"template": "..."}` (dict), which the backend rejects;
8. agents left `input_key` at the operator's library default when the user's data uses a different field name.

v2 replaces the reasoning style with **hard rules + a category cheat sheet + anti-patterns**, and adds a think-first protocol that requires emitting a structured `plan` JSON before any `create_pipeline` call. The skill is paired with a server-side change in DataFlow-WebUI that returns `use_for` / `not_for` / `examples` per operator category, so the anti-patterns live in the tool response itself rather than only in this skill.

## Use it

Drop `dataflow-pipeline-v2/` into your agent's skills directory:

```
~/.claude/skills/dataflow-pipeline-v2/
or
<project_root>/.claude/skills/dataflow-pipeline-v2/
```

The skill auto-loads when the user's request matches the trigger description (build / design / create / optimize a DataFlow pipeline).

It expects:
- a running DataFlow-WebUI backend (default `http://localhost:8000`) with the matching MCP guard changes (operator-listing endpoint that requires `category`, and a category endpoint that returns `use_for`/`not_for` guidance);
- an MCP config that whitelists the `mcp__dataflow__*` tool family.

## Evaluation snapshot

| Method                              |  n   | Time | Succ.    | Op.\,err |
|-------------------------------------|-----:|-----:|---------:|---------:|
| Direct Claude Code (no MCP, no skill)| 68 |    — |  0.0 \%  | 1.82     |
| MCP-only (no skill, MCP guard on)   | 36   | 1.4  | 36.1 \%  | 0.25     |
| DF-Agent (dev-only, wrong skill)    | 30   | 2.0  | 26.7 \%  | 1.77     |
| DF-Agent (slim skill)               | 36   | 1.3  | 30.6 \%  | 0.25     |
| **DF-Agent (this skill, v2)**       | 36   | 1.4  | **47.2 \%** | **0.22** |
| DF-Agent (legacy multi-skill suite) | 36   | 1.4  | 25.0 \%  | 0.25     |

12 tasks × 3 repetitions per condition. Time is median minutes from first agent action to first valid pipeline render. Succ.\ is the share of runs whose pipeline executes and produces at least one record matching the task's acceptance schema. Op.\,err is mean operator-selection errors per run.

The largest factor in the gain is the MCP server-side guard (jumps from 0% to 36% with no skill at all). This skill earns the additional 11 percentage points on top of that, mainly through field-flow rules and the think-first protocol, not through operator identification.

## Install / dependencies

Nothing to install for the skill itself. The runtime requirements live in DataFlow-WebUI:
- backend with the operator-categories endpoint exposing `use_for` / `not_for` / `examples`
- backend with `list_operators` that requires a `category` argument
- engine that drops unsupported run/init params and unwraps `llm_serving={"id": ...}` dicts to scalar ids

See branch `skills-agent-emnlp` of `HeRunming/DataFlow-WebUI` for the matching backend.
